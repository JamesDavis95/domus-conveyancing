"""
DATABASE MIGRATION - STEP 37 MARKETPLACE CONNECT
Add Stripe Connect fields and marketplace transaction tables
"""

from sqlalchemy import text
from database_config import engine

def upgrade_marketplace_connect_schema():
    """Add marketplace Connect fields and tables"""
    
    with engine.connect() as conn:
        try:
            # Check if we're using SQLite or PostgreSQL
            db_url = str(engine.url)
            is_sqlite = 'sqlite' in db_url
            
            # Add Stripe Connect fields to Orgs table (SQLite compatible)
            if is_sqlite:
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so check first
                cursor = conn.execute(text("PRAGMA table_info(orgs)"))
                columns = [row[1] for row in cursor]
                
                connect_columns = [
                    ('stripe_connect_account_id', 'VARCHAR(255)'),
                    ('connect_charges_enabled', 'BOOLEAN DEFAULT FALSE'),
                    ('connect_payouts_enabled', 'BOOLEAN DEFAULT FALSE'),
                    ('connect_details_submitted', 'BOOLEAN DEFAULT FALSE'),
                    ('connect_onboarded_at', 'TIMESTAMP'),
                    ('seller_rating', 'DECIMAL(3,2) DEFAULT 0.0'),
                    ('total_sales_count', 'INTEGER DEFAULT 0'),
                    ('total_revenue_pence', 'INTEGER DEFAULT 0')
                ]
                
                for col_name, col_type in connect_columns:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE orgs ADD COLUMN {col_name} {col_type}"))
                        print(f"✅ Added column {col_name} to orgs table")
            else:
                # PostgreSQL version with IF NOT EXISTS
                conn.execute(text("""
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS stripe_connect_account_id VARCHAR(255);
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS connect_charges_enabled BOOLEAN DEFAULT FALSE;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS connect_payouts_enabled BOOLEAN DEFAULT FALSE;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS connect_details_submitted BOOLEAN DEFAULT FALSE;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS connect_onboarded_at TIMESTAMP;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS seller_rating DECIMAL(3,2) DEFAULT 0.0;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS total_sales_count INTEGER DEFAULT 0;
                    ALTER TABLE orgs ADD COLUMN IF NOT EXISTS total_revenue_pence INTEGER DEFAULT 0;
                """))
            
            # Update marketplace_supply table with additional fields
            cursor = conn.execute(text("PRAGMA table_info(marketplace_supply)"))
            supply_columns = [row[1] for row in cursor]
            
            additional_supply_columns = [
                ('seller_org_id', 'INTEGER REFERENCES orgs(id)'),
                ('biodiversity_value_per_unit', 'DECIMAL(10,4) DEFAULT 0.0'),
                ('habitat_type', 'VARCHAR(100)'),
                ('supply_type', 'VARCHAR(50) DEFAULT "permanent"'),
                ('verification_status', 'VARCHAR(50) DEFAULT "pending"'),
                ('listing_expires_at', 'TIMESTAMP'),
                ('unit_type', 'VARCHAR(50) DEFAULT "biodiversity_unit"')
            ]
            
            for col_name, col_type in additional_supply_columns:
                if col_name not in supply_columns:
                    conn.execute(text(f"ALTER TABLE marketplace_supply ADD COLUMN {col_name} {col_type}"))
                    print(f"✅ Added column {col_name} to marketplace_supply table")
            
            # Create marketplace contracts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyer_org_id INTEGER REFERENCES orgs(id),
                    supply_id INTEGER REFERENCES marketplace_supply(id),
                    contract_value INTEGER NOT NULL,
                    application_fee INTEGER NOT NULL,
                    payment_intent_id VARCHAR(255) UNIQUE,
                    stripe_transfer_id VARCHAR(255),
                    transfer_status VARCHAR(50) DEFAULT 'pending',
                    status VARCHAR(50) DEFAULT 'PENDING',
                    contract_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completion_date TIMESTAMP,
                    deal_report_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create marketplace transaction events table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS marketplace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER REFERENCES contracts(id),
                    event_type VARCHAR(100) NOT NULL,
                    stripe_event_id VARCHAR(255) UNIQUE,
                    event_data TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create seller ratings table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS seller_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_org_id INTEGER REFERENCES orgs(id),
                    buyer_org_id INTEGER REFERENCES orgs(id),
                    contract_id INTEGER REFERENCES contracts(id),
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    review_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(buyer_org_id, contract_id)
                )
            """))
            
            # Create marketplace fees tracking table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS marketplace_fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER REFERENCES contracts(id),
                    application_fee_pence INTEGER NOT NULL,
                    platform_fee_pence INTEGER DEFAULT 0,
                    processing_fee_pence INTEGER DEFAULT 0,
                    fee_breakdown TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create deal reports tracking table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS deal_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER REFERENCES contracts(id) UNIQUE,
                    report_id VARCHAR(255) UNIQUE NOT NULL,
                    s3_url TEXT,
                    local_path TEXT,
                    file_size INTEGER,
                    checksum VARCHAR(64),
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """))
            
            # Create marketplace analytics cache
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS marketplace_analytics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id INTEGER REFERENCES orgs(id),
                    cache_key VARCHAR(100) NOT NULL,
                    analytics_data TEXT NOT NULL,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP DEFAULT (datetime(CURRENT_TIMESTAMP, '+1 hour')),
                    
                    UNIQUE(org_id, cache_key)
                )
            """))
            
            # Insert default marketplace configuration
            conn.execute(text("""
                INSERT OR IGNORE INTO billing_config (config_key, config_value, config_type, description, is_sensitive)
                VALUES 
                    ('marketplace_application_fee_percent', '7.0', 'decimal', 'Application fee percentage for marketplace transactions', false),
                    ('marketplace_instant_payouts_enabled', 'true', 'boolean', 'Enable instant payouts for sellers', false),
                    ('marketplace_express_onboarding_enabled', 'true', 'boolean', 'Enable Stripe Express onboarding', false),
                    ('marketplace_min_transaction_pence', '500', 'integer', 'Minimum transaction amount (£5.00)', false),
                    ('marketplace_max_transaction_pence', '100000000', 'integer', 'Maximum transaction amount (£1,000,000)', false),
                    ('marketplace_deal_report_retention_days', '2555', 'integer', 'Deal report retention period (7 years)', false),
                    ('marketplace_seller_verification_required', 'true', 'boolean', 'Require seller verification for listings', false),
                    ('marketplace_auto_payout_threshold_pence', '10000', 'integer', 'Auto payout threshold (£100)', false)
            """))
            
            # Update existing marketplace_supply records with defaults
            conn.execute(text("""
                UPDATE marketplace_supply 
                SET 
                    seller_org_id = org_id,
                    biodiversity_value_per_unit = units_available,
                    habitat_type = 'mixed',
                    supply_type = 'permanent',
                    verification_status = 'verified'
                WHERE seller_org_id IS NULL
            """))
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_orgs_connect_account ON orgs(stripe_connect_account_id)",
                "CREATE INDEX IF NOT EXISTS idx_contracts_buyer ON contracts(buyer_org_id)",
                "CREATE INDEX IF NOT EXISTS idx_contracts_supply ON contracts(supply_id)",
                "CREATE INDEX IF NOT EXISTS idx_contracts_payment_intent ON contracts(payment_intent_id)",
                "CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)",
                "CREATE INDEX IF NOT EXISTS idx_marketplace_events_contract ON marketplace_events(contract_id)",
                "CREATE INDEX IF NOT EXISTS idx_marketplace_events_stripe ON marketplace_events(stripe_event_id)",
                "CREATE INDEX IF NOT EXISTS idx_seller_ratings_seller ON seller_ratings(seller_org_id)",
                "CREATE INDEX IF NOT EXISTS idx_marketplace_fees_contract ON marketplace_fees(contract_id)",
                "CREATE INDEX IF NOT EXISTS idx_deal_reports_contract ON deal_reports(contract_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_cache_org ON marketplace_analytics_cache(org_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires ON marketplace_analytics_cache(expires_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
            
            conn.commit()
            print("✅ Marketplace Connect schema migration completed successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Marketplace Connect schema migration failed: {e}")
            raise

def downgrade_marketplace_connect_schema():
    """Remove marketplace Connect schema changes (use with caution!)"""
    
    with engine.connect() as conn:
        try:
            # Drop marketplace tables (in reverse order due to foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS marketplace_analytics_cache CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS deal_reports CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS marketplace_fees CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS seller_ratings CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS marketplace_events CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS contracts CASCADE;"))
            
            # Remove Connect columns from orgs table
            conn.execute(text("""
                ALTER TABLE orgs DROP COLUMN IF EXISTS stripe_connect_account_id;
                ALTER TABLE orgs DROP COLUMN IF EXISTS connect_charges_enabled;
                ALTER TABLE orgs DROP COLUMN IF EXISTS connect_payouts_enabled;
                ALTER TABLE orgs DROP COLUMN IF EXISTS connect_details_submitted;
                ALTER TABLE orgs DROP COLUMN IF EXISTS connect_onboarded_at;
                ALTER TABLE orgs DROP COLUMN IF EXISTS seller_rating;
                ALTER TABLE orgs DROP COLUMN IF EXISTS total_sales_count;
                ALTER TABLE orgs DROP COLUMN IF EXISTS total_revenue_pence;
            """))
            
            conn.commit()
            print("✅ Marketplace Connect schema downgrade completed")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Marketplace Connect schema downgrade failed: {e}")
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("⚠️  WARNING: This will remove all marketplace Connect data!")
        confirm = input("Type 'YES' to confirm downgrade: ")
        if confirm == "YES":
            downgrade_marketplace_connect_schema()
        else:
            print("Downgrade cancelled")
    else:
        upgrade_marketplace_connect_schema()