from database_config import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Add missing columns to existing contracts table
    try:
        cursor = conn.execute(text("PRAGMA table_info(contracts)"))
        columns = [row[1] for row in cursor]
        
        missing_columns = [
            ('buyer_org_id', 'INTEGER REFERENCES orgs(id)'),
            ('contract_value', 'INTEGER NOT NULL DEFAULT 0'),
            ('application_fee', 'INTEGER NOT NULL DEFAULT 0'),
            ('stripe_transfer_id', 'VARCHAR(255)'),
            ('transfer_status', "VARCHAR(50) DEFAULT 'pending'"),
            ('contract_date', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
            ('completion_date', 'TIMESTAMP'),
            ('deal_report_url', 'TEXT')
        ]
        
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                conn.execute(text(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Added column {col_name} to contracts table")
        
        # Now create the missing indexes
        if 'buyer_org_id' in [col[0] for col in missing_columns]:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contracts_buyer ON contracts(buyer_org_id)"))
            print("✅ Created buyer index")
        
        conn.commit()
        print("✅ Contracts table updated successfully")
        
    except Exception as e:
        print(f"❌ Failed to update contracts table: {e}")
        conn.rollback()