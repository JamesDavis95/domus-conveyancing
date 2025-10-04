"""
LIVE BILLING API ENDPOINTS - STEP 36
Production-ready Stripe billing with Bacs DD and VAT support
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import stripe
import hmac
import hashlib
import json
import logging
from datetime import datetime, timedelta
import os

from database_config import get_db
from models import Orgs, Users
from auth_oidc import get_current_user
from lib.billing.live_stripe import LiveBillingService, LiveWebhookHandler, HardQuotaEnforcer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

# Initialize services
live_billing = LiveBillingService()
webhook_handler = LiveWebhookHandler()
quota_enforcer = HardQuotaEnforcer()

# Pydantic models
class CheckoutRequest(BaseModel):
    plan: str = Field(..., regex="^(STARTER|PRO|ENTERPRISE)$")
    success_url: str
    cancel_url: str
    vat_number: Optional[str] = None

class VATValidationRequest(BaseModel):
    vat_number: str
    country_code: str = Field(..., regex="^[A-Z]{2}$")

class UsageResponse(BaseModel):
    current_usage: int
    plan_limit: int
    plan: str
    percentage_used: float
    days_until_reset: int
    overages_allowed: bool
    needs_upgrade: bool

class InvoiceItem(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    created: int
    description: str
    pdf_url: Optional[str]

class SubscriptionInfo(BaseModel):
    status: str
    plan: str
    amount: int
    currency: str
    next_billing_date: Optional[int]
    payment_method: Optional[str]
    vat_number: Optional[str]

# Utility functions
def get_org_from_user(user_id: int, db: Session) -> Orgs:
    """Get organization for user"""
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user or not user.org_id:
        raise HTTPException(status_code=400, detail="User not associated with organization")
    
    org = db.query(Orgs).filter(Orgs.id == user.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org

# Quota enforcement middleware
@router.middleware("http")
async def enforce_quotas(request: Request, call_next):
    """Enforce usage quotas for all billing-related requests"""
    response = await call_next(request)
    
    # Skip quota checks for webhooks and public endpoints
    if request.url.path.endswith("/webhook") or "public" in request.url.path:
        return response
    
    # Check if quota enforcement is needed
    if hasattr(request.state, "user_id"):
        try:
            with get_db() as db:
                user = db.query(Users).filter(Users.id == request.state.user_id).first()
                if user and user.org_id:
                    org = db.query(Orgs).filter(Orgs.id == user.org_id).first()
                    if org:
                        quota_check = await quota_enforcer.check_quota(org.id, db)
                        if quota_check["needs_upgrade"]:
                            # Add quota warning headers
                            response.headers["X-Quota-Warning"] = "true"
                            response.headers["X-Quota-Usage"] = str(quota_check["percentage_used"])
                            response.headers["X-Quota-Limit"] = str(quota_check["plan_limit"])
        except Exception as e:
            logger.warning(f"Quota check failed: {e}")
    
    return response

# Checkout endpoints
@router.post("/checkout/create")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe Checkout session with Bacs DD support"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Validate VAT number if provided
        if request.vat_number:
            vat_valid = await live_billing.validate_vat_number(
                request.vat_number, 
                request.vat_number[:2]  # Extract country code
            )
            if not vat_valid:
                raise HTTPException(status_code=400, detail="Invalid VAT number")
        
        # Create checkout session
        session_url = await live_billing.create_checkout_session(
            org_id=org.id,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            vat_number=request.vat_number,
            db=db
        )
        
        return {"checkout_url": session_url}
        
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/checkout/success")
async def checkout_success(
    session_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Handle successful checkout"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Retrieve session and update org
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.metadata.get('org_id') != str(org.id):
            raise HTTPException(status_code=403, detail="Session does not belong to organization")
        
        # Update org subscription
        org.billing_plan = session.metadata.get('plan')
        org.billing_status = 'active'
        org.billing_customer_id = session.customer
        db.commit()
        
        return {
            "success": True,
            "plan": org.billing_plan,
            "message": "Subscription activated successfully"
        }
        
    except Exception as e:
        logger.error(f"Checkout success handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Portal and management endpoints
@router.get("/portal")
async def get_billing_portal(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Stripe Customer Portal URL"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        if not org.billing_customer_id:
            raise HTTPException(status_code=400, detail="No billing account found")
        
        portal_url = await live_billing.get_billing_portal_url(
            org.id, 
            "https://your-domain.com/billing",
            db
        )
        
        return {"portal_url": portal_url}
        
    except Exception as e:
        logger.error(f"Portal access failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current subscription information"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        if not org.billing_customer_id:
            return SubscriptionInfo(
                status="none",
                plan="STARTER",
                amount=0,
                currency="gbp",
                next_billing_date=None,
                payment_method=None,
                vat_number=None
            )
        
        # Get Stripe subscription
        subscriptions = stripe.Subscription.list(customer=org.billing_customer_id, limit=1)
        
        if not subscriptions.data:
            return SubscriptionInfo(
                status="cancelled",
                plan=org.billing_plan or "STARTER",
                amount=0,
                currency="gbp",
                next_billing_date=None,
                payment_method=None,
                vat_number=org.vat_number
            )
        
        sub = subscriptions.data[0]
        
        return SubscriptionInfo(
            status=sub.status,
            plan=org.billing_plan or "STARTER",
            amount=sub.items.data[0].price.unit_amount,
            currency=sub.items.data[0].price.currency,
            next_billing_date=sub.current_period_end,
            payment_method=sub.default_payment_method,
            vat_number=org.vat_number
        )
        
    except Exception as e:
        logger.error(f"Subscription info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[InvoiceItem]:
    """Get billing invoices"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        if not org.billing_customer_id:
            return []
        
        invoices = await live_billing.get_invoices(org.id, db)
        
        return [
            InvoiceItem(
                id=inv.id,
                amount=inv.amount_paid,
                currency=inv.currency,
                status=inv.status,
                created=inv.created,
                description=inv.description or f"Subscription - {inv.lines.data[0].description}",
                pdf_url=inv.invoice_pdf
            )
            for inv in invoices.data[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Invoice retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Usage and quota endpoints
@router.get("/usage", response_model=UsageResponse)
async def get_usage_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current usage and quota information"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        quota_info = await quota_enforcer.check_quota(org.id, db)
        
        return UsageResponse(
            current_usage=quota_info["current_usage"],
            plan_limit=quota_info["plan_limit"],
            plan=quota_info["plan"],
            percentage_used=quota_info["percentage_used"],
            days_until_reset=quota_info["days_until_reset"],
            overages_allowed=quota_info["overages_allowed"],
            needs_upgrade=quota_info["needs_upgrade"]
        )
        
    except Exception as e:
        logger.error(f"Usage info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/usage/upgrade-prompt")
async def trigger_upgrade_prompt(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger upgrade prompt for quota exceeded"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        prompt_data = await quota_enforcer.get_upgrade_prompt(org.id, db)
        
        return {
            "show_prompt": True,
            "current_plan": prompt_data["current_plan"],
            "recommended_plan": prompt_data["recommended_plan"],
            "usage_percentage": prompt_data["usage_percentage"],
            "upgrade_benefits": prompt_data["upgrade_benefits"],
            "checkout_url": prompt_data.get("checkout_url")
        }
        
    except Exception as e:
        logger.error(f"Upgrade prompt failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# VAT validation endpoints
@router.post("/vat/validate")
async def validate_vat(request: VATValidationRequest):
    """Validate VAT number"""
    try:
        is_valid = await live_billing.validate_vat_number(
            request.vat_number,
            request.country_code
        )
        
        return {
            "valid": is_valid,
            "vat_number": request.vat_number,
            "country_code": request.country_code
        }
        
    except Exception as e:
        logger.error(f"VAT validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoint
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook signature
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not endpoint_secret:
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Process webhook event
        result = await webhook_handler.handle_webhook(event, db)
        
        return {"status": "success", "processed": result}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health and status endpoints
@router.get("/health")
async def billing_health():
    """Check billing system health"""
    try:
        # Test Stripe API connectivity
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        stripe.Customer.list(limit=1)  # Simple API test
        
        return {
            "status": "healthy",
            "stripe_api": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "live"
        }
        
    except Exception as e:
        logger.error(f"Billing health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "live"
        }

@router.get("/config")
async def get_billing_config(
    current_user = Depends(get_current_user)
):
    """Get billing configuration for frontend"""
    return {
        "stripe_publishable_key": os.getenv('STRIPE_PUBLISHABLE_KEY'),
        "plans": {
            "STARTER": {
                "name": "Starter",
                "price": 0,
                "currency": "gbp",
                "features": ["5 properties", "Basic search", "Email support"]
            },
            "PRO": {
                "name": "Professional",
                "price": 2900,  # £29.00
                "currency": "gbp",
                "features": ["50 properties", "Advanced search", "Priority support", "API access"]
            },
            "ENTERPRISE": {
                "name": "Enterprise",
                "price": 9900,  # £99.00
                "currency": "gbp",
                "features": ["Unlimited properties", "Custom integrations", "Dedicated support", "SLA"]
            }
        },
        "vat_enabled": True,
        "bacs_enabled": True
    }