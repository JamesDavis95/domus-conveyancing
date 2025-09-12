"""
LA Workflow API - Phase 2A Implementation
Complete workflow management for LA matters
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import get_db, engine, Base
from la.models import LAMatter, LAPayment, LASLAEvent, LAQAReview, LACommunication, LAUser
from payments import payment_engine
from sla import sla_manager
from qa import qa_workflow
from communications import communications

logger = logging.getLogger(__name__)

# Initialize database on module import
try:
    # Import all models to ensure they're registered
    from models import *
    from la.models import *
    
    Base.metadata.create_all(bind=engine)
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if 'la_matters' in inspector.get_table_names():
        logger.info("✅ Phase 2A database initialized successfully")
    else:
        logger.error("❌ LA tables not created properly")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

router = APIRouter(prefix="/workflow", tags=["workflow"])

# INTAKE & TRIAGE ENDPOINTS

@router.post("/matters/create-application")
async def create_full_application(
    applicant_name: str = Form(...),
    applicant_email: str = Form(...),
    applicant_phone: str = Form(None),
    applicant_address: str = Form(None),
    property_address: str = Form(...),
    uprn: str = Form(None),
    llc1_requested: bool = Form(False),
    con29_requested: bool = Form(True),
    con29o_requested: bool = Form(False),
    additional_enquiries: str = Form("[]"),  # JSON array
    priority: str = Form("standard"),
    property_type: str = Form("residential"),
    db: Session = Depends(get_db)
):
    """Create complete LA application with payment calculation"""
    try:
        # Create matter record
        from la.models import LAMatter
        import uuid
        
        matter_id = str(uuid.uuid4())
        matter_ref = f"LA-{datetime.now().strftime('%Y%m%d')}-{matter_id[-6:].upper()}"
        
        matter = LAMatter(
            id=matter_id,
            ref=matter_ref,
            address=property_address,
            uprn=uprn or "",
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            applicant_phone=applicant_phone,
            applicant_address=applicant_address,
            llc1_requested="true" if llc1_requested else "false",
            con29_requested="true" if con29_requested else "false", 
            con29o_requested="true" if con29o_requested else "false",
            additional_enquiries=additional_enquiries,
            priority=priority,
            status="created"
        )
        
        db.add(matter)
        
        # Calculate fees
        matter_data = {
            "llc1_requested": "true" if llc1_requested else "false",
            "con29_requested": "true" if con29_requested else "false",
            "con29o_requested": "true" if con29o_requested else "false",
            "additional_enquiries": json.loads(additional_enquiries) if additional_enquiries else [],
            "property_type": property_type
        }
        
        fee_calculation = await payment_engine.calculate_fees(matter_data)
        matter.fee_calculated = fee_calculation.get("total", 0)
        
        # Check for exemptions
        exemption_check = await payment_engine.check_exemptions({
            **matter_data,
            "applicant_type": "individual"  # Could be form field
        })
        
        if exemption_check.get("total_exemption"):
            matter.payment_status = "exemption"
            matter.exemption_reason = "; ".join(exemption_check.get("exemptions", []))
        
        # Calculate SLA dates
        sla_dates = await sla_manager.calculate_sla_dates(matter_data)
        if "due_date" in sla_dates:
            matter.sla_due_date = sla_dates["due_date"]
            matter.sla_status = "on_time"
        
        db.commit()
        
        # Create SLA tracking
        await sla_manager.create_sla_event(matter_id, "sla_started", db)
        
        # Send confirmation email
        matter_dict = {
            "id": matter_id,
            "ref": matter_ref,
            "applicant_name": applicant_name,
            "applicant_email": applicant_email,
            "address": property_address,
            "llc1_requested": "true" if llc1_requested else "false",
            "con29_requested": "true" if con29_requested else "false",
            "con29o_requested": "true" if con29o_requested else "false",
            "fee_calculated": fee_calculation.get("total", 0),
            "sla_due_date": sla_dates.get("due_date", "").isoformat() if sla_dates.get("due_date") else ""
        }
        
        await communications.send_application_received_email(matter_dict)
        await communications.log_communication(
            matter_id, "email", "outbound", applicant_email, 
            "Application received confirmation", db
        )
        
        return {
            "success": True,
            "matter_id": matter_id,
            "matter_ref": matter_ref,
            "fee_calculation": fee_calculation,
            "exemption": exemption_check,
            "sla_due_date": sla_dates.get("due_date", "").isoformat() if sla_dates.get("due_date") else "",
            "payment_required": not exemption_check.get("total_exemption", False)
        }
        
    except Exception as e:
        logger.error(f"Application creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Application creation failed: {str(e)}")

@router.post("/matters/{matter_id}/payment/create")
async def create_payment(
    matter_id: str,
    payment_method: str = Form("card"),  # card|manual|exemption
    return_url: str = Form("https://portal.council.gov.uk/payment-return"),
    manual_reference: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create payment for matter"""
    try:
        matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")
        
        if matter.payment_status == "paid":
            return {"success": False, "message": "Payment already completed"}
        
        amount = matter.fee_calculated or 0
        
        if payment_method == "card":
            # Create Gov.UK Pay payment
            payment_result = await payment_engine.create_govuk_payment(
                matter_id=matter_id,
                amount=amount,
                description=f"Local Land Charges Search - {matter.ref}",
                return_url=return_url
            )
            
            if payment_result.get("success"):
                # Create payment record
                payment = LAPayment(
                    matter_id=matter_id,
                    amount=amount,
                    provider="govuk_pay",
                    provider_payment_id=payment_result["payment_id"],
                    status="created",
                    payment_url=payment_result["payment_url"]
                )
                
                db.add(payment)
                db.commit()
                
                return {
                    "success": True,
                    "payment_id": payment.id,
                    "payment_url": payment_result["payment_url"],
                    "amount": amount
                }
            else:
                raise HTTPException(status_code=500, detail=payment_result.get("error", "Payment creation failed"))
        
        elif payment_method == "manual":
            # Process manual payment
            manual_result = await payment_engine.process_manual_payment(
                matter_id, amount, "manual", manual_reference or f"MANUAL-{matter_id}"
            )
            
            if manual_result.get("success"):
                payment = LAPayment(
                    matter_id=matter_id,
                    amount=amount,
                    provider="manual",
                    provider_payment_id=manual_result["payment_id"],
                    status="success"
                )
                
                matter.payment_status = "paid"
                matter.status = "received"
                matter.received_at = datetime.now()
                
                db.add(payment)
                db.commit()
                
                return {
                    "success": True,
                    "payment_id": payment.id,
                    "status": "completed",
                    "amount": amount
                }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid payment method")
            
    except Exception as e:
        logger.error(f"Payment creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")

@router.post("/matters/{matter_id}/payment/confirm")
async def confirm_payment(matter_id: str, payment_id: str, db: Session = Depends(get_db)):
    """Confirm payment completion (webhook/callback)"""
    try:
        payment = db.query(LAPayment).filter(
            LAPayment.matter_id == matter_id,
            LAPayment.id == payment_id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Check payment status with provider
        if payment.provider == "govuk_pay":
            status_result = await payment_engine.check_payment_status(payment.provider_payment_id)
            
            if status_result.get("success"):
                payment.status = status_result["status"]
                
                if status_result["status"] == "success" and status_result["finished"]:
                    payment.paid_at = datetime.now()
                    
                    # Update matter
                    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
                    matter.payment_status = "paid"
                    matter.status = "received"
                    matter.received_at = datetime.now()
                    
                    db.commit()
                    
                    # Send confirmation email
                    matter_dict = {
                        "ref": matter.ref,
                        "applicant_name": matter.applicant_name,
                        "applicant_email": matter.applicant_email,
                        "sla_due_date": matter.sla_due_date.isoformat() if matter.sla_due_date else ""
                    }
                    
                    payment_dict = {"amount": payment.amount}
                    
                    await communications.send_payment_confirmation_email(matter_dict, payment_dict)
                    await communications.log_communication(
                        matter_id, "email", "outbound", matter.applicant_email,
                        "Payment confirmation", db
                    )
                    
                    return {
                        "success": True,
                        "status": "paid",
                        "matter_status": "received"
                    }
        
        return {
            "success": True,
            "status": payment.status
        }
        
    except Exception as e:
        logger.error(f"Payment confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Payment confirmation failed: {str(e)}")

# WORKFLOW & ASSIGNMENT ENDPOINTS

@router.post("/matters/{matter_id}/assign")
async def assign_matter(
    matter_id: str,
    caseworker_id: str = Form(...),
    team: str = Form(None),
    db: Session = Depends(get_db)
):
    """Assign matter to caseworker"""
    try:
        matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")
        
        caseworker = db.query(LAUser).filter(LAUser.id == caseworker_id).first()
        if not caseworker:
            raise HTTPException(status_code=404, detail="Caseworker not found")
        
        # Check caseworker capacity
        current_workload = db.query(LAMatter).filter(
            LAMatter.assigned_to == caseworker_id,
            LAMatter.status.notin_(["issued", "cancelled"])
        ).count()
        
        if current_workload >= caseworker.workload_capacity:
            return {
                "success": False,
                "message": f"Caseworker at capacity ({current_workload}/{caseworker.workload_capacity})"
            }
        
        # Assign matter
        matter.assigned_to = caseworker_id
        matter.assigned_team = team or caseworker.team
        matter.status = "assigned"
        
        db.commit()
        
        return {
            "success": True,
            "assigned_to": caseworker.full_name,
            "team": matter.assigned_team,
            "workload": current_workload + 1
        }
        
    except Exception as e:
        logger.error(f"Matter assignment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Assignment failed: {str(e)}")

@router.post("/matters/{matter_id}/complete")
async def complete_matter_processing(
    matter_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Complete matter processing and trigger QA if needed"""
    try:
        matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")
        
        # Update matter status
        matter.status = "processed"
        matter.processed_at = datetime.now()
        
        # Get findings and risks for QA determination
        from la.models import LAFinding, LARisk
        findings = db.query(LAFinding).filter(LAFinding.matter_id == matter_id).all()
        risks = db.query(LARisk).filter(LARisk.matter_id == matter_id).all()
        
        matter_data = {
            "priority": matter.priority,
            "findings": [{"confidence": f.confidence or 0.8} for f in findings],
            "risks": [{"severity": r.severity} for r in risks]
        }
        
        # Get caseworker data for QA determination
        caseworker_data = {"experience_months": 12}  # Would be from user profile
        
        # Check if QA is required
        qa_check = await qa_workflow.determine_qa_requirement(matter_data, caseworker_data)
        
        if qa_check.get("qa_required"):
            # Create QA review
            review_id = await qa_workflow.create_qa_review(
                matter_id, qa_check["review_type"], db
            )
            
            if review_id:
                # Send QA notification
                review_data = {
                    "review_id": review_id,
                    "review_type": qa_check["review_type"],
                    "findings_count": len(findings)
                }
                
                # Would get reviewer email from assignment
                reviewer_email = "reviewer@council.gov.uk"
                
                background_tasks.add_task(
                    communications.send_qa_review_notification,
                    {
                        "ref": matter.ref,
                        "address": matter.address,
                        "assigned_to": matter.assigned_to
                    },
                    reviewer_email,
                    review_data
                )
                
                return {
                    "success": True,
                    "status": "qa_required",
                    "qa_review_id": review_id,
                    "qa_reasons": qa_check["reasons"]
                }
        else:
            # Auto-approve
            matter.status = "approved"
            matter.approved_at = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "status": "auto_approved",
                "qa_required": False
            }
        
        db.commit()
        return {
            "success": True,
            "status": "processing_complete",
            "qa_required": True
        }
        
    except Exception as e:
        logger.error(f"Matter completion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Completion failed: {str(e)}")

# QA WORKFLOW ENDPOINTS

@router.get("/qa/pending")
async def get_pending_qa_reviews(reviewer_id: str = None, db: Session = Depends(get_db)):
    """Get pending QA reviews"""
    try:
        reviews = await qa_workflow.get_pending_reviews(reviewer_id, db)
        return {
            "success": True,
            "reviews": reviews,
            "count": len(reviews)
        }
    except Exception as e:
        logger.error(f"Pending QA query failed: {e}")
        raise HTTPException(status_code=500, detail=f"QA query failed: {str(e)}")

@router.post("/qa/{review_id}/start")
async def start_qa_review(review_id: str, db: Session = Depends(get_db)):
    """Start QA review process"""
    try:
        success = await qa_workflow.start_review(review_id, db)
        if success:
            return {"success": True, "status": "review_started"}
        else:
            raise HTTPException(status_code=404, detail="Review not found")
    except Exception as e:
        logger.error(f"QA review start failed: {e}")
        raise HTTPException(status_code=500, detail=f"QA start failed: {str(e)}")

@router.post("/qa/{review_id}/submit")
async def submit_qa_decision(
    review_id: str,
    decision: str = Form(...),  # approved|rejected|needs_changes
    comments: str = Form(""),
    changes: str = Form("[]"),  # JSON array of changes
    db: Session = Depends(get_db)
):
    """Submit QA review decision"""
    try:
        decision_data = {
            "decision": decision,
            "comments": comments,
            "changes": json.loads(changes) if changes else []
        }
        
        success = await qa_workflow.submit_review_decision(review_id, decision_data, db)
        
        if success:
            return {
                "success": True,
                "decision": decision,
                "changes_applied": len(decision_data["changes"])
            }
        else:
            raise HTTPException(status_code=404, detail="Review not found")
            
    except Exception as e:
        logger.error(f"QA decision submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"QA submission failed: {str(e)}")

# SLA & DASHBOARD ENDPOINTS

@router.get("/dashboard/sla")
async def get_sla_dashboard(db: Session = Depends(get_db)):
    """Get SLA dashboard data"""
    try:
        overdue_matters = await sla_manager.get_overdue_matters(db)
        at_risk_matters = await sla_manager.get_at_risk_matters(db)
        qa_dashboard = await qa_workflow.get_review_dashboard_data(db)
        
        return {
            "success": True,
            "sla": {
                "overdue_count": len(overdue_matters),
                "at_risk_count": len(at_risk_matters),
                "overdue_matters": overdue_matters[:10],  # Top 10
                "at_risk_matters": at_risk_matters[:10]   # Top 10
            },
            "qa": qa_dashboard
        }
        
    except Exception as e:
        logger.error(f"Dashboard query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard failed: {str(e)}")

@router.get("/matters/{matter_id}/status")
async def get_matter_full_status(matter_id: str, db: Session = Depends(get_db)):
    """Get complete matter status including workflow, payments, SLA"""
    try:
        matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
        if not matter:
            raise HTTPException(status_code=404, detail="Matter not found")
        
        # Get payment status
        payment = db.query(LAPayment).filter(LAPayment.matter_id == matter_id).first()
        
        # Get SLA status
        sla_status = await sla_manager.check_sla_status(matter_id, db)
        
        # Get communications history
        comms = await communications.get_communication_history(matter_id, db)
        
        # Get QA review if exists
        qa_review = db.query(LAQAReview).filter(LAQAReview.matter_id == matter_id).first()
        
        return {
            "success": True,
            "matter": {
                "id": matter.id,
                "ref": matter.ref,
                "address": matter.address,
                "status": matter.status,
                "priority": matter.priority,
                "applicant": {
                    "name": matter.applicant_name,
                    "email": matter.applicant_email,
                    "phone": matter.applicant_phone
                },
                "products": {
                    "llc1": matter.llc1_requested == "true",
                    "con29": matter.con29_requested == "true", 
                    "con29o": matter.con29o_requested == "true"
                },
                "workflow": {
                    "assigned_to": matter.assigned_to,
                    "created_at": matter.created_at.isoformat(),
                    "received_at": matter.received_at.isoformat() if matter.received_at else None,
                    "processed_at": matter.processed_at.isoformat() if matter.processed_at else None,
                    "approved_at": matter.approved_at.isoformat() if matter.approved_at else None,
                    "issued_at": matter.issued_at.isoformat() if matter.issued_at else None
                }
            },
            "payment": {
                "status": matter.payment_status,
                "amount": matter.fee_calculated,
                "method": payment.provider if payment else None,
                "paid_at": payment.paid_at.isoformat() if payment and payment.paid_at else None
            },
            "sla": sla_status,
            "qa_review": {
                "required": qa_review is not None,
                "status": qa_review.status if qa_review else None,
                "reviewer": qa_review.reviewer_name if qa_review else None
            },
            "communications": comms
        }
        
    except Exception as e:
        logger.error(f"Matter status query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status query failed: {str(e)}")