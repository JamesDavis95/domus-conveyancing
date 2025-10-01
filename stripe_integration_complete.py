"""
Complete Stripe Integration for Domus Planning Platform
Handles subscription billing, payment processing, marketplace payouts, and plan management
"""

import stripe
import os
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models import User, Organization, Subscription, Payment, get_db
from backend_auth_complete import PlanType, PLAN_PRICING
import json

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_51234567890abcdef')  # TODO: Set in production
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_1234567890abcdef')

class StripeService:
    """Complete Stripe service for billing and payments"""
    
    @staticmethod
    async def create_customer(user: User, organization: Organization) -> str:
        """Create a Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    "user_id": user.id,
                    "org_id": organization.id,
                    "organization_name": organization.name
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create customer: {str(e)}"
            )
    
    @staticmethod
    async def create_subscription(
        customer_id: str, 
        plan_type: PlanType,
        trial_days: int = 14
    ) -> Dict[str, Any]:
        """Create a new subscription"""
        try:
            # Get plan pricing
            plan_config = PLAN_PRICING[plan_type]
            
            # Create price if it doesn't exist
            price = stripe.Price.create(
                currency=plan_config["currency"],
                unit_amount=plan_config["amount"],
                recurring={"interval": plan_config["interval"]},
                product_data={
                    "name": plan_config["name"],
                    "description": plan_config["description"]
                }
            )
            
            # Create subscription with trial
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price.id}],
                trial_period_days=trial_days,
                metadata={
                    "plan_type": plan_type.value
                }
            )
            
            return {
                "subscription_id": subscription.id,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "trial_end": datetime.fromtimestamp(subscription.trial_end) if subscription.trial_end else None
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create subscription: {str(e)}"
            )
    
    @staticmethod
    async def update_subscription(subscription_id: str, new_plan_type: PlanType) -> Dict[str, Any]:
        """Update subscription to new plan"""
        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get new plan pricing
            plan_config = PLAN_PRICING[new_plan_type]
            
            # Create new price
            new_price = stripe.Price.create(
                currency=plan_config["currency"],
                unit_amount=plan_config["amount"],
                recurring={"interval": plan_config["interval"]},
                product_data={
                    "name": plan_config["name"],
                    "description": plan_config["description"]
                }
            )
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": new_price.id
                }],
                proration_behavior="immediate_bill",
                metadata={
                    "plan_type": new_plan_type.value
                }
            )
            
            return {
                "subscription_id": updated_subscription.id,
                "status": updated_subscription.status,
                "current_period_start": datetime.fromtimestamp(updated_subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(updated_subscription.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update subscription: {str(e)}"
            )
    
    @staticmethod
    async def cancel_subscription(subscription_id: str, immediate: bool = False) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "canceled_at": datetime.fromtimestamp(subscription.canceled_at) if subscription.canceled_at else None,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
    
    @staticmethod
    async def create_payment_intent(
        customer_id: str,
        amount: int,
        currency: str = "gbp",
        description: str = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payments"""
        try:
            payment_intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=amount,
                currency=currency,
                description=description,
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create payment intent: {str(e)}"
            )
    
    @staticmethod
    async def create_setup_intent(customer_id: str) -> Dict[str, Any]:
        """Create setup intent for saving payment methods"""
        try:
            setup_intent = stripe.SetupIntent.create(
                customer=customer_id,
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "setup_intent_id": setup_intent.id,
                "client_secret": setup_intent.client_secret,
                "status": setup_intent.status
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create setup intent: {str(e)}"
            )
    
    @staticmethod
    async def get_payment_methods(customer_id: str) -> List[Dict[str, Any]]:
        """Get customer's saved payment methods"""
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )
            
            return [{
                "id": pm.id,
                "type": pm.type,
                "card": {
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year
                } if pm.card else None
            } for pm in payment_methods.data]
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get payment methods: {str(e)}"
            )
    
    @staticmethod
    async def create_marketplace_account(
        email: str,
        business_name: str,
        country: str = "GB"
    ) -> Dict[str, Any]:
        """Create Stripe Express account for marketplace sellers"""
        try:
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True}
                },
                business_type="individual",
                metadata={
                    "business_name": business_name
                }
            )
            
            return {
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create marketplace account: {str(e)}"
            )
    
    @staticmethod
    async def create_account_link(account_id: str, return_url: str, refresh_url: str) -> str:
        """Create account onboarding link"""
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                return_url=return_url,
                refresh_url=refresh_url,
                type="account_onboarding"
            )
            
            return account_link.url
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create account link: {str(e)}"
            )
    
    @staticmethod
    async def create_marketplace_payment(
        customer_id: str,
        amount: int,
        seller_account_id: str,
        application_fee: int,
        description: str = None
    ) -> Dict[str, Any]:
        """Create payment with marketplace fee"""
        try:
            payment_intent = stripe.PaymentIntent.create(
                customer=customer_id,
                amount=amount,
                currency="gbp",
                description=description,
                application_fee_amount=application_fee,
                transfer_data={
                    "destination": seller_account_id
                },
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "application_fee": application_fee,
                "seller_amount": amount - application_fee,
                "status": payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create marketplace payment: {str(e)}"
            )
    
    @staticmethod
    async def get_billing_portal_url(customer_id: str, return_url: str) -> str:
        """Create billing portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create billing portal: {str(e)}"
            )

class WebhookHandler:
    """Handle Stripe webhook events"""
    
    @staticmethod
    async def handle_webhook(request: Request, db: Session):
        """Process incoming Stripe webhooks"""
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle different event types
        if event['type'] == 'customer.subscription.created':
            await WebhookHandler._handle_subscription_created(event['data']['object'], db)
        elif event['type'] == 'customer.subscription.updated':
            await WebhookHandler._handle_subscription_updated(event['data']['object'], db)
        elif event['type'] == 'customer.subscription.deleted':
            await WebhookHandler._handle_subscription_deleted(event['data']['object'], db)
        elif event['type'] == 'invoice.payment_succeeded':
            await WebhookHandler._handle_payment_succeeded(event['data']['object'], db)
        elif event['type'] == 'invoice.payment_failed':
            await WebhookHandler._handle_payment_failed(event['data']['object'], db)
        
        return {"status": "success"}
    
    @staticmethod
    async def _handle_subscription_created(subscription_data: Dict, db: Session):
        """Handle subscription creation"""
        customer_id = subscription_data['customer']
        
        # Find organization by customer ID
        organization = db.query(Organization).filter(
            Organization.stripe_customer_id == customer_id
        ).first()
        
        if organization:
            # Create subscription record
            subscription = Subscription(
                org_id=organization.id,
                stripe_subscription_id=subscription_data['id'],
                plan_type=PlanType(subscription_data['metadata'].get('plan_type', 'core')),
                status=subscription_data['status'],
                current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
                current_period_end=datetime.fromtimestamp(subscription_data['current_period_end'])
            )
            db.add(subscription)
            
            # Update organization subscription status
            organization.subscription_status = subscription_data['status']
            db.commit()
    
    @staticmethod
    async def _handle_subscription_updated(subscription_data: Dict, db: Session):
        """Handle subscription updates"""
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
            
            if subscription_data.get('canceled_at'):
                subscription.cancelled_at = datetime.fromtimestamp(subscription_data['canceled_at'])
            
            # Update organization
            subscription.organization.subscription_status = subscription_data['status']
            db.commit()
    
    @staticmethod
    async def _handle_subscription_deleted(subscription_data: Dict, db: Session):
        """Handle subscription cancellation"""
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.utcnow()
            subscription.organization.subscription_status = "cancelled"
            db.commit()
    
    @staticmethod
    async def _handle_payment_succeeded(invoice_data: Dict, db: Session):
        """Handle successful payment"""
        customer_id = invoice_data['customer']
        
        # Find organization
        organization = db.query(Organization).filter(
            Organization.stripe_customer_id == customer_id
        ).first()
        
        if organization:
            # Create payment record
            payment = Payment(
                org_id=organization.id,
                stripe_invoice_id=invoice_data['id'],
                amount=invoice_data['amount_paid'],
                currency=invoice_data['currency'],
                status="succeeded"
            )
            db.add(payment)
            db.commit()
    
    @staticmethod
    async def _handle_payment_failed(invoice_data: Dict, db: Session):
        """Handle failed payment"""
        customer_id = invoice_data['customer']
        
        # Find organization
        organization = db.query(Organization).filter(
            Organization.stripe_customer_id == customer_id
        ).first()
        
        if organization:
            # Create payment record
            payment = Payment(
                org_id=organization.id,
                stripe_invoice_id=invoice_data['id'],
                amount=invoice_data['amount_due'],
                currency=invoice_data['currency'],
                status="failed"
            )
            db.add(payment)
            
            # Update subscription status
            organization.subscription_status = "past_due"
            db.commit()

# Billing API endpoints
class BillingAPI:
    """Billing management endpoints"""
    
    @staticmethod
    async def get_billing_info(user: User, db: Session) -> Dict[str, Any]:
        """Get current billing information"""
        organization = user.organization
        
        # Get current subscription
        current_subscription = db.query(Subscription).filter(
            Subscription.org_id == organization.id,
            Subscription.status.in_(["active", "trialing", "past_due"])
        ).first()
        
        # Get recent payments
        recent_payments = db.query(Payment).filter(
            Payment.org_id == organization.id
        ).order_by(Payment.created_at.desc()).limit(5).all()
        
        return {
            "organization": {
                "name": organization.name,
                "plan_type": organization.plan_type.value,
                "subscription_status": organization.subscription_status.value,
                "trial_end": organization.trial_end.isoformat() if organization.trial_end else None
            },
            "subscription": {
                "id": current_subscription.stripe_subscription_id if current_subscription else None,
                "status": current_subscription.status if current_subscription else None,
                "current_period_start": current_subscription.current_period_start.isoformat() if current_subscription else None,
                "current_period_end": current_subscription.current_period_end.isoformat() if current_subscription else None
            } if current_subscription else None,
            "recent_payments": [{
                "amount": payment.amount / 100,  # Convert from pence
                "currency": payment.currency.upper(),
                "status": payment.status,
                "date": payment.created_at.isoformat()
            } for payment in recent_payments]
        }
    
    @staticmethod
    async def create_subscription(
        user: User,
        plan_type: PlanType,
        db: Session
    ) -> Dict[str, Any]:
        """Create new subscription"""
        organization = user.organization
        
        if not organization.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found"
            )
        
        # Create subscription
        subscription_data = await StripeService.create_subscription(
            organization.stripe_customer_id,
            plan_type
        )
        
        # Update organization
        organization.plan_type = plan_type
        db.commit()
        
        return subscription_data
    
    @staticmethod
    async def update_subscription(
        user: User,
        new_plan_type: PlanType,
        db: Session
    ) -> Dict[str, Any]:
        """Update existing subscription"""
        organization = user.organization
        
        # Get current subscription
        current_subscription = db.query(Subscription).filter(
            Subscription.org_id == organization.id,
            Subscription.status == "active"
        ).first()
        
        if not current_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        # Update subscription
        subscription_data = await StripeService.update_subscription(
            current_subscription.stripe_subscription_id,
            new_plan_type
        )
        
        # Update organization
        organization.plan_type = new_plan_type
        db.commit()
        
        return subscription_data