"""
Stripe Integration for Domus Planning Platform
Handles subscription billing, payment processing, and plan management
"""

import stripe
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import User, Organization, Subscription, Payment
from backend_auth import PlanType

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_...')  # TODO: Set in production
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_...')

# Plan configuration matching our pricing
STRIPE_PLANS = {
    PlanType.CORE: {
        'price_id': 'price_core_monthly',  # TODO: Create in Stripe Dashboard
        'amount': 80000,  # £800 in pence
        'currency': 'gbp',
        'interval': 'month',
        'name': 'Core Plan'
    },
    PlanType.PROFESSIONAL: {
        'price_id': 'price_professional_monthly',  # TODO: Create in Stripe Dashboard  
        'amount': 250000,  # £2,500 in pence
        'currency': 'gbp',
        'interval': 'month',
        'name': 'Professional Plan'
    },
    PlanType.ENTERPRISE: {
        'price_id': 'price_enterprise_monthly',  # TODO: Create in Stripe Dashboard
        'amount': 750000,  # £7,500 in pence
        'currency': 'gbp',
        'interval': 'month',
        'name': 'Enterprise Plan'
    }
}

class StripeService:
    """Service class for all Stripe operations"""
    
    @staticmethod
    async def create_customer(user: User, organization: Organization) -> str:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    'user_id': user.id,
                    'org_id': organization.id,
                    'org_name': organization.name
                }
            )
            
            # Save customer ID to organization
            organization.stripe_customer_id = customer.id
            
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create customer: {str(e)}"
            )
    
    @staticmethod
    async def create_checkout_session(
        org_id: int, 
        plan_type: str, 
        success_url: str, 
        cancel_url: str,
        db: Session
    ) -> str:
        """Create Stripe checkout session for plan upgrade"""
        
        # Get organization
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Ensure customer exists
        if not org.stripe_customer_id:
            user = db.query(User).filter(User.org_id == org_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No user found for organization"
                )
            org.stripe_customer_id = await StripeService.create_customer(user, org)
            db.commit()
        
        # Get plan details
        plan_config = STRIPE_PLANS.get(plan_type)
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan type: {plan_type}"
            )
        
        try:
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=org.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_config['price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    'org_id': org_id,
                    'plan_type': plan_type
                },
                allow_promotion_codes=True,
                billing_address_collection='required',
                automatic_tax={'enabled': True},
            )
            
            return session.url
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create checkout session: {str(e)}"
            )
    
    @staticmethod
    async def handle_subscription_created(subscription_data: Dict, db: Session):
        """Handle successful subscription creation webhook"""
        org_id = int(subscription_data['metadata'].get('org_id'))
        plan_type = subscription_data['metadata'].get('plan_type')
        
        # Update organization plan
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            org.plan_type = plan_type
            org.subscription_status = 'active'
            
            # Create subscription record
            subscription = Subscription(
                org_id=org_id,
                stripe_subscription_id=subscription_data['id'],
                plan_type=plan_type,
                status='active',
                current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
                current_period_end=datetime.fromtimestamp(subscription_data['current_period_end']),
                created_at=datetime.utcnow()
            )
            
            db.add(subscription)
            db.commit()
    
    @staticmethod
    async def handle_invoice_payment_succeeded(invoice_data: Dict, db: Session):
        """Handle successful invoice payment webhook"""
        customer_id = invoice_data['customer']
        
        # Find organization by customer ID
        org = db.query(Organization).filter(Organization.stripe_customer_id == customer_id).first()
        if not org:
            return
        
        # Create payment record
        payment = Payment(
            org_id=org.id,
            stripe_invoice_id=invoice_data['id'],
            amount=invoice_data['amount_paid'],
            currency=invoice_data['currency'],
            status='succeeded',
            created_at=datetime.utcnow()
        )
        
        db.add(payment)
        db.commit()
    
    @staticmethod
    async def handle_subscription_deleted(subscription_data: Dict, db: Session):
        """Handle subscription cancellation webhook"""
        stripe_subscription_id = subscription_data['id']
        
        # Update subscription status
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.cancelled_at = datetime.utcnow()
            
            # Downgrade organization to core plan
            org = db.query(Organization).filter(Organization.id == subscription.org_id).first()
            if org:
                org.plan_type = PlanType.CORE
                org.subscription_status = 'cancelled'
            
            db.commit()
    
    @staticmethod
    async def cancel_subscription(org_id: int, db: Session) -> bool:
        """Cancel organization subscription"""
        subscription = db.query(Subscription).filter(
            Subscription.org_id == org_id,
            Subscription.status == 'active'
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        try:
            # Cancel in Stripe
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            
            # Update local records
            subscription.status = 'cancelled'
            subscription.cancelled_at = datetime.utcnow()
            
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if org:
                org.plan_type = PlanType.CORE
                org.subscription_status = 'cancelled'
            
            db.commit()
            return True
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
    
    @staticmethod
    async def get_billing_portal_url(org_id: int, return_url: str, db: Session) -> str:
        """Create Stripe billing portal session"""
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org or not org.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No billing account found"
            )
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=org.stripe_customer_id,
                return_url=return_url
            )
            return session.url
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create billing portal: {str(e)}"
            )
    
    @staticmethod
    async def get_usage_based_billing(org_id: int, db: Session) -> Dict[str, Any]:
        """Calculate usage-based billing for API calls"""
        # For enterprise customers who exceed API limits
        from backend_auth import get_user_usage
        
        org = db.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            return {}
        
        usage_stats = await get_user_usage(None, org_id, db)
        
        # Calculate overages
        overages = {}
        overage_cost = 0
        
        for resource_type, usage in usage_stats['usage'].items():
            if usage['limit'] != 'unlimited' and usage['current'] > usage['limit']:
                excess = usage['current'] - usage['limit']
                cost_per_unit = {
                    'site_analyses': 50,  # £50 per excess analysis
                    'documents': 25,      # £25 per excess document
                    'api_calls': 0.01     # £0.01 per excess API call
                }.get(resource_type, 0)
                
                overage_amount = excess * cost_per_unit
                overages[resource_type] = {
                    'excess': excess,
                    'cost_per_unit': cost_per_unit,
                    'total_cost': overage_amount
                }
                overage_cost += overage_amount
        
        return {
            'total_overage_cost': overage_cost,
            'overages': overages,
            'billing_cycle': usage_stats['month_start']
        }

# Webhook signature verification
def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Stripe webhook signature"""
    try:
        stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
        return True
    except (ValueError, stripe.error.SignatureVerificationError):
        return False

# Utility functions for plan management
def get_plan_features(plan_type: str) -> Dict[str, Any]:
    """Get plan features and limits"""
    from backend_auth import PLAN_LIMITS
    
    base_features = PLAN_LIMITS.get(plan_type, PLAN_LIMITS[PlanType.CORE])
    plan_config = STRIPE_PLANS.get(plan_type, {})
    
    return {
        'name': plan_config.get('name', 'Unknown Plan'),
        'price': plan_config.get('amount', 0) / 100,  # Convert pence to pounds
        'features': base_features,
        'stripe_price_id': plan_config.get('price_id')
    }

def calculate_proration(current_plan: str, new_plan: str, days_remaining: int) -> int:
    """Calculate proration amount for plan changes"""
    current_price = STRIPE_PLANS.get(current_plan, {}).get('amount', 0)
    new_price = STRIPE_PLANS.get(new_plan, {}).get('amount', 0)
    
    # Daily rate difference
    daily_difference = (new_price - current_price) / 30
    
    # Proration amount in pence
    proration = int(daily_difference * days_remaining)
    
    return max(0, proration)  # No negative prorations