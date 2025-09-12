"""
Phase 2B: Bulk Data Processing & Migration System
================================================

Priority 1: Bulk matter import and processing
"""
import asyncio
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, BackgroundTasks
from la.models import LAMatter
from la.workflow import create_full_application
from payments import payment_engine
from sla import sla_manager

router = APIRouter(prefix="/bulk", tags=["Bulk Processing"])

class BulkProcessor:
    """Handle bulk import of existing LA matters and documents"""
    
    def __init__(self):
        self.batch_size = 50
        self.max_concurrent = 10
        
    async def import_matters_from_csv(self, csv_file: UploadFile, db: Session) -> Dict[str, Any]:
        """
        Import bulk matters from CSV export
        Expected columns: ref, applicant_name, applicant_email, property_address, llc1_requested, con29_requested
        """
        df = pd.read_csv(csv_file.file)
        
        results = {
            "total_rows": len(df),
            "processed": 0,
            "errors": [],
            "matters_created": []
        }
        
        # Process in batches
        for batch_start in range(0, len(df), self.batch_size):
            batch = df.iloc[batch_start:batch_start + self.batch_size]
            
            # Create semaphore for concurrent processing
            sem = asyncio.Semaphore(self.max_concurrent)
            
            async def process_row(row_data):
                async with sem:
                    try:
                        matter = await self._create_matter_from_row(row_data, db)
                        results["matters_created"].append(matter.id)
                        results["processed"] += 1
                    except Exception as e:
                        results["errors"].append(f"Row {row_data.name}: {str(e)}")
            
            # Process batch concurrently
            tasks = [process_row(row) for _, row in batch.iterrows()]
            await asyncio.gather(*tasks)
            
        return results
    
    async def _create_matter_from_row(self, row_data: pd.Series, db: Session) -> LAMatter:
        """Create LAMatter from CSV row data"""
        matter_data = {
            "ref": row_data.get("ref", f"BULK-{row_data.name}"),
            "applicant_name": row_data.get("applicant_name", ""),
            "applicant_email": row_data.get("applicant_email", ""),
            "property_address": row_data.get("property_address", ""),
            "llc1_requested": str(row_data.get("llc1_requested", "true")).lower() == "true",
            "con29_requested": str(row_data.get("con29_requested", "true")).lower() == "true",
            "priority": row_data.get("priority", "standard")
        }
        
        # Use existing workflow system
        result = await create_full_application(
            applicant_name=matter_data["applicant_name"],
            applicant_email=matter_data["applicant_email"],
            property_address=matter_data["property_address"],
            llc1_requested=matter_data["llc1_requested"],
            con29_requested=matter_data["con29_requested"],
            priority=matter_data["priority"],
            db=db
        )
        
        return db.query(LAMatter).filter(LAMatter.id == result["matter_id"]).first()
    
    async def bulk_document_processing(self, matter_ids: List[str], document_folder: str, db: Session):
        """
        Process documents in bulk for existing matters
        Looks for files named: {matter_ref}_LLC1.pdf, {matter_ref}_CON29.pdf
        """
        import os
        from la.services import parse_and_store
        
        results = {"processed": 0, "errors": []}
        
        for matter_id in matter_ids:
            matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
            if not matter:
                continue
                
            # Look for documents
            llc1_path = os.path.join(document_folder, f"{matter.ref}_LLC1.pdf")
            con29_path = os.path.join(document_folder, f"{matter.ref}_CON29.pdf") 
            
            docs = []
            if os.path.exists(llc1_path):
                with open(llc1_path, 'rb') as f:
                    docs.append(("LLC1", f.read()))
            if os.path.exists(con29_path):
                with open(con29_path, 'rb') as f:
                    docs.append(("CON29", f.read()))
                    
            if docs:
                try:
                    parse_and_store(db, matter, docs)
                    results["processed"] += 1
                except Exception as e:
                    results["errors"].append(f"Matter {matter.ref}: {str(e)}")
                    
        return results

@router.post("/import-matters")
async def import_bulk_matters(
    csv_file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Import matters from CSV file"""
    processor = BulkProcessor()
    
    # Process in background
    background_tasks.add_task(
        processor.import_matters_from_csv,
        csv_file,
        db
    )
    
    return {"status": "Import started", "check_status_at": "/bulk/status"}

@router.post("/process-documents")
async def bulk_process_documents(
    matter_ids: List[str],
    document_folder: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)  
):
    """Process documents in bulk for existing matters"""
    processor = BulkProcessor()
    
    background_tasks.add_task(
        processor.bulk_document_processing,
        matter_ids,
        document_folder,
        db
    )
    
    return {"status": "Bulk processing started"}