"""
Database debug endpoint
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import inspect
from db import engine, Base
from models import *
from la.models import *

router = APIRouter()

@router.post("/debug/init-db")
async def init_database():
    """Initialize database with all Phase 2A tables"""
    try:
        # Drop and recreate all tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        la_tables = [t for t in tables if t.startswith('la_')]
        
        result = {
            "success": True,
            "total_tables": len(tables),
            "la_tables": la_tables,
            "all_tables": sorted(tables)
        }
        
        if 'la_matters' in tables:
            columns = inspector.get_columns('la_matters')
            applicant_cols = [c['name'] for c in columns if 'applicant' in c['name']]
            result["la_matters_columns"] = len(columns)
            result["applicant_fields"] = applicant_cols
            
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/debug/db-status")
async def database_status():
    """Check current database status"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        result = {
            "tables_exist": len(tables),
            "la_matters_exists": 'la_matters' in tables,
            "all_tables": sorted(tables)
        }
        
        if 'la_matters' in tables:
            columns = inspector.get_columns('la_matters')
            result["la_matters_columns"] = [c['name'] for c in columns]
            
        return result
        
    except Exception as e:
        return {"error": str(e)}