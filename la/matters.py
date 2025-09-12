
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
import io
import uuid
import logging
from la.models import LAMatter, LAFinding
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter(prefix="/la/matters")



# Import get_db from db module 
# (get_db function is already defined in db.py)


@router.post("/ingest")
async def ingest(
	file: UploadFile = File(None),
	files: list[UploadFile] = File(None),
	titleNo: str = Form(None),
	addr: str = Form(None),
	uprn: str = Form(None),
	db: Session = Depends(get_db),
):
	logger = logging.getLogger("la.matters.ingest")
	logger.info(f"Received ingest request: titleNo={titleNo}, addr={addr}, uprn={uprn}, file={file}, files={files}")
	upload_files = []
	if file is not None:
		upload_files.append(file)
	if files is not None:
		if isinstance(files, list):
			upload_files.extend([f for f in files if f is not None])
		else:
			upload_files.append(files)
	if not upload_files:
		logger.error(f"No file(s) uploaded. file={file}, files={files}")
		raise HTTPException(status_code=400, detail="No file(s) uploaded. Please provide a PDF file.")
	upload = upload_files[0]
	try:
		contents = await upload.read()
		pdf_reader = PdfReader(io.BytesIO(contents))
		text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
	except Exception as e:
		logger.error(f"PDF extraction failed: {e}")
		text = f"PDF extraction failed: {e}"
	matter_id = str(uuid.uuid4())
	ref_value = titleNo or f"AUTO-{matter_id[:8]}"
	matter = LAMatter(
		id=matter_id,
		ref=ref_value,
		address=addr or "",
		uprn=uprn or "",
	)
	try:
		db.add(matter)
		db.commit()
		db.refresh(matter)
		finding = LAFinding(
			matter_id=matter.id,
			key="pdf_text",
			value=text[:10000],
		)
		db.add(finding)
		db.commit()
	except Exception as e:
		logger.error(f"Failed to create LAMatter or LAFinding: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to create matter or finding: {e}")
	summary = {
		"id": matter.id,
		"ref": matter.ref,
		"address": matter.address,
		"uprn": matter.uprn,
		"created_at": matter.created_at.isoformat() if matter.created_at else None,
		"extracted_text": text[:500],
	}
	logger.info(f"Ingest summary: {summary}")
	return summary

# List all LA Matters
@router.post("/create")
async def create_matter(
	titleNo: str = Form(None),
	addr: str = Form(None),
	uprn: str = Form(None),
	db: Session = Depends(get_db),
):
	logger = logging.getLogger("la.matters.create")
	matter_id = str(uuid.uuid4())
	ref_value = titleNo or f"AUTO-{matter_id[:8]}"
	matter = LAMatter(
		id=matter_id,
		ref=ref_value,
		address=addr or "",
		uprn=uprn or "",
	)
	try:
		db.add(matter)
		db.commit()
		db.refresh(matter)
	except Exception as e:
		logger.error(f"Failed to create LAMatter: {e}")
		raise HTTPException(status_code=500, detail=f"Failed to create matter: {e}")
	summary = {
		"id": matter.id,
		"ref": matter.ref,
		"address": matter.address,
		"uprn": matter.uprn,
		"created_at": matter.created_at.isoformat() if matter.created_at else None,
	}
	logger.info(f"Create summary: {summary}")
	return summary
@router.post("/{mid}/property")
async def set_property(mid: str, request: Request, db: Session = Depends(get_db)):
	body = await request.json()
	matter = db.query(LAMatter).filter(LAMatter.id == mid).first()
	if not matter:
		raise HTTPException(404, "Matter not found")
	
	# Update matter with property details
	if "address_text" in body:
		matter.address = body["address_text"]
	if "uprn" in body:
		matter.uprn = body["uprn"]
	
	db.commit()
	return {"ok": True}

@router.get("/{mid}/summary")
async def get_summary(mid: str):
    """Get summary of property search with AI-extracted data"""
    
    # Try to load AI-extracted data first
    import os, json
    cache_file = f"data/uploads/{mid}_extracted.json"
    
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                extracted_data = json.load(f)
            
            # Use AI-extracted data with fallbacks
            risk_indicators = extracted_data.get("risk_indicators", [])
            property_details = extracted_data.get("property_details", {})
            
            # Calculate risk summary
            high_risks = len([r for r in risk_indicators if r.get("level") == "High"])
            medium_risks = len([r for r in risk_indicators if r.get("level") == "Medium"])
            total_risks = len(risk_indicators)
            
            # Determine overall risk level
            if high_risks > 0:
                overall_risk = "High"
            elif medium_risks > 0:
                overall_risk = "Medium"  
            else:
                overall_risk = "Low"
            
            summary = {
                "llc1": extracted_data.get("llc1", {}),
                "con29": extracted_data.get("con29", {}),
                "risk_indicators": risk_indicators,
                "property_details": {
                    "filename": extracted_data.get("processing_info", {}).get("filename", ""),
                    "council": property_details.get("council", ""),
                    "address": property_details.get("address", ""),
                    "postcode": property_details.get("postcode", "")
                },
                "data_source": "AI_EXTRACTED",
                "summary": {
                    "total_issues": total_risks,
                    "high_priority": high_risks,
                    "medium_priority": medium_risks,
                    "overall_risk_level": overall_risk,
                    "ai_confidence": "High" if extracted_data.get("llc1") and extracted_data.get("con29") else "Medium"
                }
            }
            
            return JSONResponse(summary)
            
        except Exception as e:
            # Fall through to default data if extraction file is corrupted
            pass
    
    # Default fallback data if no AI extraction available
    summary = {
        "llc1": {
            "LISTED_BUILDING": "No entries found",
            "CONSERVATION_AREA": "Awaiting AI analysis",
            "TREE_PRESERVATION_ORDER": "Awaiting AI analysis", 
            "FINANCIAL_CHARGES": "Awaiting AI analysis",
            "CIL": "Awaiting AI analysis"
        },
        "con29": {
            "ROAD_STATUS": "Awaiting AI analysis",
            "PLANNING_REFS_STRICT": "Awaiting AI analysis",
            "ENFORCEMENT_NOTICES": "Awaiting AI analysis",
            "DRAINAGE_WITHIN_3M": "Awaiting AI analysis",
            "BUILD_OVER_AGREEMENT": "Awaiting AI analysis", 
            "LANDFILL_WITHIN_250M": "Awaiting AI analysis"
        },
        "data_source": "DEFAULT_TEMPLATE",
        "summary": {
            "total_issues": 0,
            "high_priority": 0,
            "message": "Upload PDF documents for AI-powered analysis"
        }
    }
    
    return JSONResponse(summary)

@router.get("/matters/{mid}/findings")
async def get_findings(mid: str, db: Session = Depends(get_db)):
    """Get structured findings for a matter from database"""
    from .models import LAFinding, LARisk, LAFile
    
    # Get findings
    findings = db.query(LAFinding).filter(LAFinding.matter_id == mid).all()
    
    # Get risks  
    risks = db.query(LARisk).filter(LARisk.matter_id == mid).all()
    
    # Get files
    files = db.query(LAFile).filter(LAFile.matter_id == mid).all()
    
    return JSONResponse({
        "findings": [
            {
                "id": f.id,
                "key": f.key,
                "value": f.value,
                "confidence": f.confidence,
                "evidence_file": f.evidence_file,
                "created_at": f.created_at.isoformat() if f.created_at else None
            } for f in findings
        ],
        "risks": [
            {
                "id": r.id,
                "code": r.code,
                "severity": r.severity,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in risks
        ],
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "kind": f.kind,
                "processing_status": f.processing_status,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                "processed_at": f.processed_at.isoformat() if f.processed_at else None
            } for f in files
        ],
        "summary": {
            "total_findings": len(findings),
            "total_risks": len(risks),
            "high_risks": len([r for r in risks if r.severity == "HIGH"]),
            "medium_risks": len([r for r in risks if r.severity == "MEDIUM"]),
            "low_risks": len([r for r in risks if r.severity == "LOW"]),
            "files_uploaded": len(files),
            "files_processed": len([f for f in files if f.processing_status == "completed"])
        }
    })

@router.get("/list")
async def list_matters(db: Session = Depends(get_db)):
	matters = db.query(LAMatter).order_by(LAMatter.created_at.desc()).all()
	return {"matters": [
		{"id": m.id, "ref": m.ref, "address": m.address, "created_at": m.created_at.isoformat() if m.created_at else None}
		for m in matters
	]}
