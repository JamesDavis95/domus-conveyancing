from database_config import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check contracts table structure
    result = conn.execute(text("PRAGMA table_info(contracts)"))
    columns = [row[1] for row in result]
    print("Contracts table columns:", columns)
    
    # Create indexes only if columns exist
    if 'buyer_org_id' in columns:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contracts_buyer ON contracts(buyer_org_id)"))
        print("✅ Created buyer index")
    
    if 'supply_id' in columns:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contracts_supply ON contracts(supply_id)"))
        print("✅ Created supply index")
    
    if 'payment_intent_id' in columns:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contracts_payment_intent ON contracts(payment_intent_id)"))
        print("✅ Created payment intent index")
    
    if 'status' in columns:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)"))
        print("✅ Created status index")
    
    conn.commit()
    print("✅ Marketplace Connect indexes completed")