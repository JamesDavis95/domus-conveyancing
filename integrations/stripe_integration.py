"""
Stripe Integration with API Keys
Handles payments, subscriptions, credits, and webhooks exactly as specified
"""

import os
import stripe
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime
import hmac
import hashlib

logger = logging.getLogger(__name__)

# Initialize Stripe with secret key (server-side only)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Stripe Price IDs from environment
STRIPE_PRICES = {
    "DEV": os.getenv("STRIPE_PRICE_DEV"),
    "DEV_PRO": os.getenv("STRIPE_PRICE_DEV_PRO"), 
    "CONSULTANT": os.getenv("STRIPE_PRICE_CONSULTANT"),
    "ENTERPRISE": os.getenv("STRIPE_PRICE_ENTERPRISE"),
    "CREDITS_AI": os.getenv("STRIPE_PRICE_CREDITS_AI"),
    "CREDITS_DOC": os.getenv("STRIPE_PRICE_CREDITS_DOC"),
    "CREDITS_BUNDLE": os.getenv("STRIPE_PRICE_CREDITS_BUNDLE")
}

router = APIRouter(prefix="/api/billing", tags=["Billing"])

class StripeService:
    """Stripe integration service following exact specifications"""
    
    def __init__(self):
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
    async def create_checkout_session(self, 
                                    price_id: str, 
                                    customer_email: str,
                                    org_id: str,
                                    success_url: str,
                                    cancel_url: str) -> Dict[str, Any]:
        """Create Stripe Checkout session for plans or credits"""
        
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription' if price_id in [
                    STRIPE_PRICES["DEV"], 
                    STRIPE_PRICES["DEV_PRO"], 
                    STRIPE_PRICES["CONSULTANT"], 
                    STRIPE_PRICES["ENTERPRISE"]
                ] else 'payment',
                customer_email=customer_email,
                metadata={
                    'org_id': org_id,
                    'price_type': self._get_price_type(price_id)
                },
                success_url=success_url,
                cancel_url=cancel_url,
                allow_promotion_codes=True
            )
            
            return {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe checkout error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    def _get_price_type(self, price_id: str) -> str:
        """Map price ID to type for webhook processing"""
        price_map = {
            STRIPE_PRICES["DEV"]: "plan_dev",
            STRIPE_PRICES["DEV_PRO"]: "plan_dev_pro", 
            STRIPE_PRICES["CONSULTANT"]: "plan_consultant",
            STRIPE_PRICES["ENTERPRISE"]: "plan_enterprise",
            STRIPE_PRICES["CREDITS_AI"]: "credits_ai",
            STRIPE_PRICES["CREDITS_DOC"]: "credits_doc",
            STRIPE_PRICES["CREDITS_BUNDLE"]: "credits_bundle"
        }
        return price_map.get(price_id, "unknown")
    
    async def verify_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature"""
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
            
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    async def process_checkout_completed(self, session: Dict[str, Any]):
        """Process completed checkout - update org plan/credits"""
        
        org_id = session['metadata']['org_id']
        price_type = session['metadata']['price_type']
        
        # Update organization based on purchase type
        if price_type.startswith('plan_'):
            await self._update_organization_plan(org_id, price_type)
        elif price_type.startswith('credits_'):
            await self._add_organization_credits(org_id, price_type)
        
        logger.info(f"Updated org {org_id} for {price_type}")
    
    async def _update_organization_plan(self, org_id: str, plan_type: str):
        """Update organization subscription plan and quotas"""
        from lib.pricing import SubscriptionPlan, PricingService
        
        # Map Stripe plan to our internal plan
        plan_mapping = {
            "plan_dev": SubscriptionPlan.DEV,
            "plan_dev_pro": SubscriptionPlan.DEV_PRO,
            "plan_consultant": SubscriptionPlan.CONSULTANT,
            "plan_enterprise": SubscriptionPlan.ENTERPRISE
        }
        
        new_plan = plan_mapping.get(plan_type)
        if not new_plan:
            logger.error(f"Unknown plan type: {plan_type}")
            return
        
        pricing_service = PricingService()
        await pricing_service.update_organization_plan(org_id, new_plan)
    
    async def _add_organization_credits(self, org_id: str, credit_type: str):
        """Add credits to organization balance"""
        from lib.quota import QuotaManager, CreditType
        
        # Credit amounts (10x packs as specified)
        credit_amounts = {
            "credits_ai": {"type": CreditType.AI_ANALYSIS, "amount": 10},
            "credits_doc": {"type": CreditType.AUTO_DOCS, "amount": 10},
            "credits_bundle": {"type": CreditType.SUBMISSION_BUNDLES, "amount": 10}
        }
        
        credit_info = credit_amounts.get(credit_type)
        if not credit_info:
            logger.error(f"Unknown credit type: {credit_type}")
            return
        
        quota_manager = QuotaManager()
        await quota_manager.add_credits(
            org_id, 
            credit_info["type"], 
            credit_info["amount"]
        )

# Initialize service
stripe_service = StripeService()

# Routes
@router.post("/checkout")
async def create_checkout(request: Request):
    """Create Stripe checkout session"""
    body = await request.json()
    
    # Validate required fields
    required_fields = ["price_type", "org_id", "customer_email"]
    for field in required_fields:
        if field not in body:
            raise HTTPException(status_code=400, detail=f"Missing {field}")
    
    price_type = body["price_type"]
    price_id = STRIPE_PRICES.get(price_type.upper())
    
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid price type: {price_type}")
    
    # Create checkout session
    result = await stripe_service.create_checkout_session(
        price_id=price_id,
        customer_email=body["customer_email"],
        org_id=body["org_id"],
        success_url=body.get("success_url", "https://app.domusplanning.co.uk/billing/success"),
        cancel_url=body.get("cancel_url", "https://app.domusplanning.co.uk/billing/cancel")
    )
    
    return result

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks - updates plans and credits automatically"""
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Verify webhook
    event = await stripe_service.verify_webhook(payload, signature)
    
    # Process specific events
    if event['type'] == 'checkout.session.completed':
        await stripe_service.process_checkout_completed(event['data']['object'])
        
    elif event['type'] == 'customer.subscription.created':
        # Handle new subscription
        subscription = event['data']['object']
        logger.info(f"New subscription created: {subscription['id']}")
        
    elif event['type'] == 'customer.subscription.updated':
        # Handle subscription changes
        subscription = event['data']['object']
        logger.info(f"Subscription updated: {subscription['id']}")
        
    elif event['type'] == 'customer.subscription.deleted':
        # Handle subscription cancellation
        subscription = event['data']['object']
        logger.info(f"Subscription cancelled: {subscription['id']}")
        
    elif event['type'] == 'invoice.paid':
        # Handle successful payment
        invoice = event['data']['object']
        logger.info(f"Invoice paid: {invoice['id']}")
        
    elif event['type'] == 'invoice.payment_failed':
        # Handle failed payment
        invoice = event['data']['object']
        logger.warning(f"Payment failed: {invoice['id']}")
        
    elif event['type'] == 'payment_intent.succeeded':
        # Handle one-time payment success
        payment_intent = event['data']['object']
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        
    elif event['type'] == 'charge.refunded':
        # Handle refund
        charge = event['data']['object']
        logger.info(f"Charge refunded: {charge['id']}")
    
    return {"status": "success"}

@router.get("/plans")
async def get_pricing_plans():
    """Get available pricing plans with Stripe price IDs"""
    
    plans = [
        {
            "name": "Developer",
            "price": "£199",
            "interval": "month",
            "stripe_price_id": STRIPE_PRICES["DEV"],
            "features": [
                "2 projects",
                "500 API calls/month", 
                "Development Calculator",
                "Basic support"
            ]
        },
        {
            "name": "Developer Pro", 
            "price": "£399",
            "interval": "month",
            "stripe_price_id": STRIPE_PRICES["DEV_PRO"],
            "features": [
                "10 projects",
                "2,000 API calls/month",
                "Development Calculator",
                "Scheme Optimiser", 
                "Priority support"
            ]
        },
        {
            "name": "Consultant",
            "price": "£999", 
            "interval": "month",
            "stripe_price_id": STRIPE_PRICES["CONSULTANT"],
            "features": [
                "Unlimited projects",
                "Unlimited API calls",
                "All premium modules",
                "Planning Copilot",
                "Submit-to-Council",
                "Dedicated support"
            ]
        },
        {
            "name": "Enterprise",
            "price": "£25,000",
            "interval": "year", 
            "stripe_price_id": STRIPE_PRICES["ENTERPRISE"],
            "features": [
                "White-label solution",
                "Custom integrations", 
                "SLA guarantees",
                "Dedicated account manager",
                "Custom training"
            ]
        }
    ]
    
    return {"plans": plans}

@router.get("/credits")
async def get_credit_packs():
    """Get available credit packs"""
    
    credit_packs = [
        {
            "name": "AI Analysis Credits",
            "description": "10× AI Analysis credits",
            "price": "£400",
            "stripe_price_id": STRIPE_PRICES["CREDITS_AI"],
            "credits": 10,
            "type": "AI_ANALYSIS"
        },
        {
            "name": "Document Generation Credits", 
            "description": "10× Auto-Doc credits",
            "price": "£1,000",
            "stripe_price_id": STRIPE_PRICES["CREDITS_DOC"],
            "credits": 10,
            "type": "AUTO_DOCS"
        },
        {
            "name": "Submission Bundle Credits",
            "description": "10× Submission Bundle credits", 
            "price": "£1,000",
            "stripe_price_id": STRIPE_PRICES["CREDITS_BUNDLE"],
            "credits": 10,
            "type": "SUBMISSION_BUNDLES"
        }
    ]
    
    return {"credit_packs": credit_packs}

# Export for use in main app
__all__ = ["router", "stripe_service", "STRIPE_PRICES"]