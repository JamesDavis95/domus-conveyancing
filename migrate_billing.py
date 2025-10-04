"""
DATABASE MIGRATION - STEP 36 LIVE BILLING
Add billing fields for live Stripe integration with VAT and usage tracking
"""

from sqlalchemy import text
from database_config import engine

def upgrade_billing_schema():
    """Add billing fields to support live Stripe integration"""
    
    with engine.connect() as conn:
        try:
            # Check if we're using SQLite or PostgreSQL
            db_url = str(engine.url)
            is_sqlite = 'sqlite' in db_url
            
            # Add billing fields to Orgs table (SQLite compatible)
            if is_sqlite:
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so check first
                cursor = conn.execute(text("PRAGMA table_info(orgs)"))
                columns = [row[1] for row in cursor]
                
                billing_columns = [
                    ('billing_subscription_id', 'VARCHAR(255)'),
                    ('billing_plan', "VARCHAR(50) DEFAULT 'STARTER'"),
                    ('billing_status', "VARCHAR(50) DEFAULT 'active'"),
                    ('vat_number', 'VARCHAR(50)'),
                    ('billing_country', "VARCHAR(2) DEFAULT 'GB'"),
                    ('billing_currency', "VARCHAR(3) DEFAULT 'gbp'"),
                    ('subscription_current_period_start', 'INTEGER'),
                    ('subscription_current_period_end', 'INTEGER'),
                    ('trial_end_date', 'TIMESTAMP'),
                    ('payment_method_type', 'VARCHAR(50)'),
                    ('billing_email', 'VARCHAR(255)'),
                    ('tax_exempt', 'BOOLEAN DEFAULT FALSE')
                ]
                
                for col_name, col_type in billing_columns:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE orgs ADD COLUMN {col_name} {col_type}"))
                        print(f"✅ Added column {col_name} to orgs table")
            else:
                # PostgreSQL version with IF NOT EXISTS
                conn.execute(text("""
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_subscription_id VARCHAR(255);
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_plan VARCHAR(50) DEFAULT 'STARTER';
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_status VARCHAR(50) DEFAULT 'active';
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS vat_number VARCHAR(50);
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_country VARCHAR(2) DEFAULT 'GB';
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_currency VARCHAR(3) DEFAULT 'gbp';
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS subscription_current_period_start INTEGER;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS subscription_current_period_end INTEGER;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMP;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS payment_method_type VARCHAR(50);
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS billing_email VARCHAR(255);
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS tax_exempt BOOLEAN DEFAULT FALSE;
                """))
            
            # Create billing events table for audit trail
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS billing_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    event_type VARCHAR(100) NOT NULL,
                    stripe_event_id VARCHAR(255) UNIQUE,
                    event_data TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create usage tracking table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    billing_period_start DATE NOT NULL,
                    billing_period_end DATE NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    quota_limit INTEGER DEFAULT 0,
                    overage_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(org_id, billing_period_start, resource_type)
                )
            """))
            
            # Create invoice cache table for performance
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS invoice_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    stripe_invoice_id VARCHAR(255) UNIQUE NOT NULL,
                    invoice_number VARCHAR(100),
                    amount INTEGER NOT NULL,
                    currency VARCHAR(3) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_timestamp INTEGER NOT NULL,
                    paid_timestamp INTEGER,
                    pdf_url TEXT,
                    description TEXT,
                    subscription_id VARCHAR(255),
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+1 hour'))
                )
            """))
            
            # Create quota violations table for monitoring
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quota_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    resource_type VARCHAR(50) NOT NULL,
                    attempted_usage INTEGER NOT NULL,
                    quota_limit INTEGER NOT NULL,
                    violation_percentage DECIMAL(5,2),
                    action_taken VARCHAR(100),
                    user_id INTEGER,
                    endpoint VARCHAR(255),
                    user_agent TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create subscription changes audit table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS subscription_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    change_type VARCHAR(50) NOT NULL,
                    old_plan VARCHAR(50),
                    new_plan VARCHAR(50),
                    old_status VARCHAR(50),
                    new_status VARCHAR(50),
                    effective_date TIMESTAMP,
                    stripe_subscription_id VARCHAR(255),
                    proration_amount INTEGER,
                    changed_by_user_id INTEGER,
                    change_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create VAT validation cache
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vat_validation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vat_number VARCHAR(50) NOT NULL,
                    country_code VARCHAR(2) NOT NULL,
                    is_valid BOOLEAN NOT NULL,
                    company_name VARCHAR(255),
                    company_address TEXT,
                    validation_source VARCHAR(50),
                    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+24 hours')),
                    
                    UNIQUE(vat_number, country_code)
                )
            """))
            
            # Create billing configuration table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS billing_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value TEXT NOT NULL,
                    config_type VARCHAR(50) DEFAULT 'string',
                    description TEXT,
                    is_sensitive BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Insert default billing configuration
            conn.execute(text("""
                INSERT OR IGNORE INTO billing_config (config_key, config_value, config_type, description, is_sensitive)
                VALUES 
                    ('vat_rate', '0.20', 'decimal', 'UK VAT rate (20%)', false),
                    ('quota_warning_threshold', '0.80', 'decimal', 'Send warning when 80% of quota used', false),
                    ('quota_critical_threshold', '0.95', 'decimal', 'Send critical alert when 95% of quota used', false),
                    ('overage_grace_period_days', '3', 'integer', 'Grace period for overages before enforcement', false),
                    ('webhook_timeout_seconds', '30', 'integer', 'Webhook processing timeout', false),
                    ('billing_cache_ttl_seconds', '300', 'integer', 'Billing data cache TTL (5 minutes)', false),
                    ('enable_bacs_direct_debit', 'true', 'boolean', 'Enable Bacs Direct Debit payments', false),
                    ('require_vat_for_eu', 'true', 'boolean', 'Require VAT number for EU customers', false),
                    ('force_sca_authentication', 'true', 'boolean', 'Force Strong Customer Authentication', false),
                    ('default_currency', 'gbp', 'string', 'Default billing currency', false),
                    ('supported_currencies', 'gbp,eur,usd', 'string', 'Supported billing currencies', false)
            """))
            
            # Insert default quota limits for existing organizations
            conn.execute(text("""
                INSERT OR IGNORE INTO usage_tracking (org_id, billing_period_start, billing_period_end, resource_type, quota_limit)
                SELECT 
                    id as org_id,
                    date('now', 'start of month') as billing_period_start,
                    date('now', 'start of month', '+1 month', '-1 day') as billing_period_end,
                    resource_type,
                    CASE 
                        WHEN COALESCE(billing_plan, 'STARTER') = 'STARTER' THEN
                            CASE resource_type
                                WHEN 'properties' THEN 5
                                WHEN 'api_calls' THEN 100
                                WHEN 'documents' THEN 5
                                WHEN 'submission_packs' THEN 1
                                ELSE 0
                            END
                        WHEN billing_plan = 'PRO' THEN
                            CASE resource_type
                                WHEN 'properties' THEN 50
                                WHEN 'api_calls' THEN 1000
                                WHEN 'documents' THEN 50
                                WHEN 'submission_packs' THEN 10
                                ELSE 0
                            END
                        WHEN billing_plan = 'ENTERPRISE' THEN
                            CASE resource_type
                                WHEN 'properties' THEN 999999
                                WHEN 'api_calls' THEN 10000
                                WHEN 'documents' THEN 500
                                WHEN 'submission_packs' THEN 100
                                ELSE 0
                            END
                        ELSE 0
                    END as quota_limit
                FROM orgs
                CROSS JOIN (
                    SELECT 'properties' as resource_type
                    UNION SELECT 'api_calls'
                    UNION SELECT 'documents' 
                    UNION SELECT 'submission_packs'
                ) AS resource_types
            """))
            
            conn.commit()
            print("✅ Billing schema migration completed successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Billing schema migration failed: {e}")
            raise

def downgrade_billing_schema():
    """Remove billing schema changes (use with caution!)"""
    
    with engine.connect() as conn:
        try:
            # Drop billing tables (in reverse order due to foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS billing_config CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS vat_validation_cache CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS subscription_changes CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS quota_violations CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS invoice_cache CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS usage_tracking CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS billing_events CASCADE;"))
            
            # Remove billing columns from orgs table
            conn.execute(text("""
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_customer_id;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_subscription_id;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_plan;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_status;
                ALTER TABLE orgs DROP COLUMN IF EXISTS vat_number;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_country;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_currency;
                ALTER TABLE orgs DROP COLUMN IF EXISTS subscription_current_period_start;
                ALTER TABLE orgs DROP COLUMN IF EXISTS subscription_current_period_end;
                ALTER TABLE orgs DROP COLUMN IF EXISTS trial_end_date;
                ALTER TABLE orgs DROP COLUMN IF EXISTS payment_method_type;
                ALTER TABLE orgs DROP COLUMN IF EXISTS billing_email;
                ALTER TABLE orgs DROP COLUMN IF EXISTS tax_exempt;
            """))
            
            conn.commit()
            print("✅ Billing schema downgrade completed")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Billing schema downgrade failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("⚠️  WARNING: This will remove all billing data!")
        confirm = input("Type 'YES' to confirm downgrade: ")
        if confirm == "YES":
            downgrade_billing_schema()
        else:
            print("Downgrade cancelled")
    else:
        upgrade_billing_schema()