"""
MARKETPLACE CONNECT API ENDPOINTS - STEP 37
Stripe Connect Express onboarding and marketplace payment processing
with 7% application fees and automated seller payouts
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import stripe
import logging
from datetime import datetime

from database_config import SessionLocal
from models import Orgs, Users, MarketplaceSupply, Contracts
from auth_oidc import get_current_user
from lib.marketplace.stripe_connect import StripeConnectService, MarketplaceWebhookHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

# Initialize services
connect_service = StripeConnectService()
webhook_handler = MarketplaceWebhookHandler()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class ConnectOnboardingRequest(BaseModel):
    business_type: str = Field(default="individual", regex="^(individual|company)$")
    refresh_url: str
    return_url: str

class MarketplacePaymentRequest(BaseModel):
    marketplace_supply_id: int
    amount_pence: int
    seller_account_id: str
    currency: str = "gbp"

class InstantPayoutRequest(BaseModel):
    account_id: str
    amount_pence: int
    currency: str = "gbp"

class ConnectAccountResponse(BaseModel):
    account_id: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    onboarding_url: Optional[str] = None

class MarketplaceTransactionResponse(BaseModel):
    transaction_id: str
    amount_pence: int
    application_fee_pence: int
    seller_amount_pence: int
    status: str
    payment_url: Optional[str] = None

class MarketplaceAnalyticsResponse(BaseModel):
    total_sales: int
    total_revenue_pence: int
    total_fees_paid_pence: int
    total_purchases: int
    total_spent_pence: int
    recent_transactions: List[Dict[str, Any]]

def get_org_from_user(user_id: int, db: Session) -> Orgs:
    """Get organization for user"""
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user or not user.org_id:
        raise HTTPException(status_code=400, detail="User not associated with organization")
    
    org = db.query(Orgs).filter(Orgs.id == user.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return org

# Connect account management endpoints
@router.post("/connect/onboard", response_model=ConnectAccountResponse)
async def create_connect_account(
    request: ConnectOnboardingRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe Express account and get onboarding link"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Check if account already exists
        if org.stripe_connect_account_id:
            # Get existing account status
            account_status = await connect_service.get_account_status(org.stripe_connect_account_id)
            
            # Create new onboarding link if needed
            onboarding_url = None
            if not account_status['details_submitted']:
                onboarding_url = await connect_service.create_account_link(
                    org.stripe_connect_account_id,
                    request.refresh_url,
                    request.return_url
                )
            
            return ConnectAccountResponse(
                account_id=account_status['id'],
                charges_enabled=account_status['charges_enabled'],
                payouts_enabled=account_status['payouts_enabled'],
                details_submitted=account_status['details_submitted'],
                onboarding_url=onboarding_url
            )
        
        # Create new Express account
        account_result = await connect_service.create_express_account(
            current_user.id,
            request.business_type,
            db
        )
        
        # Create onboarding link
        onboarding_url = await connect_service.create_account_link(
            account_result['account_id'],
            request.refresh_url,
            request.return_url
        )
        
        return ConnectAccountResponse(
            account_id=account_result['account_id'],
            charges_enabled=account_result['charges_enabled'],
            payouts_enabled=account_result['payouts_enabled'],
            details_submitted=account_result['details_submitted'],
            onboarding_url=onboarding_url
        )
        
    except Exception as e:
        logger.error(f"Connect onboarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connect/status", response_model=ConnectAccountResponse)
async def get_connect_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current Connect account status"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        if not org.stripe_connect_account_id:
            raise HTTPException(status_code=404, detail="No Connect account found")
        
        account_status = await connect_service.get_account_status(org.stripe_connect_account_id)
        
        return ConnectAccountResponse(
            account_id=account_status['id'],
            charges_enabled=account_status['charges_enabled'],
            payouts_enabled=account_status['payouts_enabled'],
            details_submitted=account_status['details_submitted']
        )
        
    except Exception as e:
        logger.error(f"Connect status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connect/refresh-onboarding")
async def refresh_onboarding_link(
    refresh_url: str,
    return_url: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh onboarding link for incomplete accounts"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        if not org.stripe_connect_account_id:
            raise HTTPException(status_code=404, detail="No Connect account found")
        
        onboarding_url = await connect_service.create_account_link(
            org.stripe_connect_account_id,
            refresh_url,
            return_url
        )
        
        return {"onboarding_url": onboarding_url}
        
    except Exception as e:
        logger.error(f"Onboarding link refresh failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Marketplace payment endpoints
@router.post("/payments/create", response_model=MarketplaceTransactionResponse)
async def create_marketplace_payment(
    request: MarketplacePaymentRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create marketplace payment with application fee"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Verify marketplace supply exists and is available
        supply = db.query(MarketplaceSupply).filter(MarketplaceSupply.id == request.marketplace_supply_id).first()
        if not supply:
            raise HTTPException(status_code=404, detail="Marketplace supply not found")
        
        if supply.status != 'AVAILABLE':
            raise HTTPException(status_code=400, detail="Supply not available for purchase")
        
        # Verify seller has valid Connect account
        seller_org = db.query(Orgs).filter(Orgs.stripe_connect_account_id == request.seller_account_id).first()
        if not seller_org:
            raise HTTPException(status_code=400, detail="Invalid seller account")
        
        # Create payment intent with application fee
        payment_result = await connect_service.create_marketplace_payment_intent(
            amount_pence=request.amount_pence,
            seller_account_id=request.seller_account_id,
            buyer_org_id=org.id,
            marketplace_supply_id=request.marketplace_supply_id,
            currency=request.currency,
            db=db
        )
        
        return MarketplaceTransactionResponse(
            transaction_id=payment_result['payment_intent_id'],
            amount_pence=payment_result['amount'],
            application_fee_pence=payment_result['application_fee'],
            seller_amount_pence=payment_result['seller_amount'],
            status=payment_result['status'],
            payment_url=f"https://js.stripe.com/v3/#{payment_result['client_secret']}"
        )
        
    except Exception as e:
        logger.error(f"Marketplace payment creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payments/confirm/{payment_intent_id}")
async def confirm_marketplace_payment(
    payment_intent_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm marketplace payment and execute transfer"""
    try:
        # Confirm payment and create contract
        result = await connect_service.confirm_payment_and_transfer(payment_intent_id, db)
        
        # Generate deal report
        deal_report_url = await connect_service.generate_deal_report(result['contract_id'], db)
        
        return {
            "success": True,
            "contract_id": result['contract_id'],
            "payment_intent_id": result['payment_intent_id'],
            "amount_paid": result['amount_paid'],
            "application_fee": result['application_fee'],
            "seller_amount": result['seller_amount'],
            "deal_report_url": deal_report_url
        }
        
    except Exception as e:
        logger.error(f"Payment confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contracts")
async def get_marketplace_contracts(
    limit: int = 20,
    offset: int = 0,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get marketplace contracts for organization"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Get contracts where org is buyer or seller
        contracts = db.query(Contracts).join(
            MarketplaceSupply, Contracts.supply_id == MarketplaceSupply.id
        ).filter(
            (Contracts.buyer_org_id == org.id) | (MarketplaceSupply.seller_org_id == org.id)
        ).order_by(Contracts.contract_date.desc()).offset(offset).limit(limit).all()
        
        contract_list = []
        for contract in contracts:
            supply = db.query(MarketplaceSupply).filter(MarketplaceSupply.id == contract.supply_id).first()
            buyer_org = db.query(Orgs).filter(Orgs.id == contract.buyer_org_id).first()
            seller_org = db.query(Orgs).filter(Orgs.id == supply.seller_org_id).first() if supply else None
            
            contract_list.append({
                "contract_id": contract.id,
                "amount_pence": contract.contract_value,
                "application_fee_pence": contract.application_fee,
                "seller_amount_pence": contract.contract_value - contract.application_fee,
                "status": contract.status,
                "contract_date": contract.contract_date.isoformat() if contract.contract_date else None,
                "payment_intent_id": contract.payment_intent_id,
                "deal_report_url": contract.deal_report_url,
                "buyer_org_name": buyer_org.name if buyer_org else "Unknown",
                "seller_org_name": seller_org.name if seller_org else "Unknown",
                "biodiversity_units": float(supply.biodiversity_value_per_unit) if supply else None,
                "habitat_type": supply.habitat_type if supply else None,
                "is_buyer": contract.buyer_org_id == org.id,
                "is_seller": supply.seller_org_id == org.id if supply else False
            })
        
        return {
            "contracts": contract_list,
            "total_count": len(contract_list),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Contract retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=MarketplaceAnalyticsResponse)
async def get_marketplace_analytics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get marketplace analytics for organization"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        analytics = await connect_service.get_marketplace_analytics(org.id, db)
        
        return MarketplaceAnalyticsResponse(
            total_sales=analytics['seller_analytics']['total_sales'],
            total_revenue_pence=analytics['seller_analytics']['total_revenue_pence'],
            total_fees_paid_pence=analytics['seller_analytics']['total_fees_paid_pence'],
            total_purchases=analytics['buyer_analytics']['total_purchases'],
            total_spent_pence=analytics['buyer_analytics']['total_spent_pence'],
            recent_transactions=analytics['recent_transactions']
        )
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Payout endpoints
@router.post("/payouts/instant")
async def create_instant_payout(
    request: InstantPayoutRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create instant payout to seller account"""
    try:
        org = get_org_from_user(current_user.id, db)
        
        # Verify account ownership
        if org.stripe_connect_account_id != request.account_id:
            raise HTTPException(status_code=403, detail="Account does not belong to organization")
        
        payout_result = await connect_service.create_instant_payout(
            request.account_id,
            request.amount_pence,
            request.currency
        )
        
        return {
            "payout_id": payout_result['payout_id'],
            "amount_pence": payout_result['amount'],
            "currency": payout_result['currency'],
            "status": payout_result['status'],
            "arrival_date": payout_result['arrival_date']
        }
        
    except Exception as e:
        logger.error(f"Instant payout failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook endpoint
@router.post("/webhook/connect")
async def stripe_connect_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe Connect webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook signature
        endpoint_secret = os.getenv('STRIPE_CONNECT_WEBHOOK_SECRET')
        if not endpoint_secret:
            raise HTTPException(status_code=500, detail="Connect webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Process webhook event
        event_type = event['type']
        success = False
        
        if event_type == 'account.updated':
            success = await webhook_handler.handle_account_updated(event, db)
        elif event_type == 'payment_intent.succeeded':
            success = await webhook_handler.handle_payment_intent_succeeded(event, db)
        elif event_type == 'transfer.created':
            success = await webhook_handler.handle_transfer_created(event, db)
        else:
            logger.info(f"Unhandled Connect webhook event: {event_type}")
            success = True  # Don't fail for unhandled events
        
        return {"status": "success", "processed": success, "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Connect webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health and configuration endpoints
@router.get("/health")
async def marketplace_health():
    """Check marketplace system health"""
    try:
        # Test Stripe API connectivity
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        stripe.Account.list(limit=1)  # Simple API test
        
        return {
            "status": "healthy",
            "stripe_connect_api": "connected",
            "application_fee_percent": connect_service.APPLICATION_FEE_PERCENT,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "connect_v1"
        }
        
    except Exception as e:
        logger.error(f"Marketplace health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "connect_v1"
        }

@router.get("/config")
async def get_marketplace_config():
    """Get marketplace configuration for frontend"""
    return {
        "stripe_publishable_key": os.getenv('STRIPE_PUBLISHABLE_KEY'),
        "application_fee_percent": connect_service.APPLICATION_FEE_PERCENT,
        "supported_currencies": ["gbp", "eur", "usd"],
        "instant_payouts_enabled": True,
        "express_onboarding_enabled": True,
        "marketplace_features": {
            "biodiversity_trading": True,
            "automated_transfers": True,
            "deal_reports": True,
            "analytics_dashboard": True
        }
    }