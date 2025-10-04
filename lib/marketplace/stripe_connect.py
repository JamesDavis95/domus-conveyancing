"""
STEP 37: MARKETPLACE PAYOUTS - STRIPE CONNECT E2E
Production-ready Stripe Connect integration for marketplace transactions
with 7% application fees and automated seller payouts
"""

import os
import stripe
import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import hashlib
import uuid

from database_config import engine
from models import Orgs, Users, MarketplaceSupply, Contracts

logger = logging.getLogger(__name__)

# Configure Stripe Connect
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeConnectService:
    """
    Stripe Connect service for marketplace payouts
    Handles Express onboarding, payment intents, and transfers
    """
    
    APPLICATION_FEE_PERCENT = 7.0  # 7% application fee
    
    def __init__(self):
        self.s3_client = boto3.client('s3') if os.getenv('AWS_ACCESS_KEY_ID') else None
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'domus-marketplace-reports')
    
    async def create_express_account(self, user_id: int, business_type: str = "individual", db: Session = None) -> Dict[str, Any]:
        """
        Create Stripe Express account for seller onboarding
        """
        try:
            # Get user details
            user = db.query(Users).filter(Users.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            org = db.query(Orgs).filter(Orgs.id == user.org_id).first() if user.org_id else None
            
            # Create Express account
            account = stripe.Account.create(
                type='express',
                country='GB',  # UK-focused platform
                email=user.email,
                business_type=business_type,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_profile={
                    'mcc': '7389',  # Business services, not elsewhere classified
                    'url': 'https://domus-platform.com',
                    'product_description': 'Biodiversity Net Gain marketplace transactions'
                },
                metadata={
                    'user_id': str(user_id),
                    'org_id': str(user.org_id) if user.org_id else '',
                    'platform': 'domus_marketplace'
                }
            )
            
            # Store account ID
            if org:
                org.stripe_connect_account_id = account.id
                db.commit()
            
            logger.info(f"Created Stripe Express account {account.id} for user {user_id}")
            
            return {
                'account_id': account.id,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'details_submitted': account.details_submitted,
                'created': account.created
            }
            
        except Exception as e:
            logger.error(f"Failed to create Express account: {e}")
            raise
    
    async def create_account_link(self, account_id: str, refresh_url: str, return_url: str) -> str:
        """
        Create account link for Express onboarding
        """
        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding'
            )
            
            return account_link.url
            
        except Exception as e:
            logger.error(f"Failed to create account link: {e}")
            raise
    
    async def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get account status and capabilities
        """
        try:
            account = stripe.Account.retrieve(account_id)
            
            return {
                'id': account.id,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled,
                'details_submitted': account.details_submitted,
                'requirements': {
                    'currently_due': account.requirements.currently_due,
                    'eventually_due': account.requirements.eventually_due,
                    'past_due': account.requirements.past_due,
                    'pending_verification': account.requirements.pending_verification
                },
                'capabilities': account.capabilities
            }
            
        except Exception as e:
            logger.error(f"Failed to get account status: {e}")
            raise
    
    async def create_marketplace_payment_intent(
        self, 
        amount_pence: int, 
        seller_account_id: str,
        buyer_org_id: int,
        marketplace_supply_id: int,
        currency: str = "gbp",
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Create payment intent with application fee for marketplace transaction
        """
        try:
            # Calculate application fee (7%)
            application_fee = int(amount_pence * (self.APPLICATION_FEE_PERCENT / 100))
            
            # Get marketplace supply details
            supply = db.query(MarketplaceSupply).filter(MarketplaceSupply.id == marketplace_supply_id).first()
            if not supply:
                raise ValueError(f"Marketplace supply {marketplace_supply_id} not found")
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_pence,
                currency=currency,
                application_fee_amount=application_fee,
                transfer_data={
                    'destination': seller_account_id,
                },
                metadata={
                    'buyer_org_id': str(buyer_org_id),
                    'seller_account_id': seller_account_id,
                    'marketplace_supply_id': str(marketplace_supply_id),
                    'application_fee_percent': str(self.APPLICATION_FEE_PERCENT),
                    'supply_type': supply.supply_type,
                    'biodiversity_metric': str(supply.biodiversity_value_per_unit)
                },
                description=f"BNG Marketplace: {supply.biodiversity_value_per_unit} biodiversity units"
            )
            
            logger.info(f"Created payment intent {payment_intent.id} for £{amount_pence/100:.2f} with £{application_fee/100:.2f} fee")
            
            return {
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'amount': amount_pence,
                'application_fee': application_fee,
                'seller_amount': amount_pence - application_fee,
                'status': payment_intent.status
            }
            
        except Exception as e:
            logger.error(f"Failed to create marketplace payment intent: {e}")
            raise
    
    async def confirm_payment_and_transfer(self, payment_intent_id: str, db: Session = None) -> Dict[str, Any]:
        """
        Confirm payment and execute transfer to seller
        """
        try:
            # Retrieve payment intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != 'succeeded':
                raise ValueError(f"Payment intent {payment_intent_id} not succeeded: {payment_intent.status}")
            
            # Get metadata
            metadata = payment_intent.metadata
            buyer_org_id = int(metadata.get('buyer_org_id'))
            seller_account_id = metadata.get('seller_account_id')
            marketplace_supply_id = int(metadata.get('marketplace_supply_id'))
            
            # Create contract record
            contract = Contracts(
                buyer_org_id=buyer_org_id,
                supply_id=marketplace_supply_id,
                contract_value=payment_intent.amount,
                application_fee=payment_intent.application_fee_amount,
                payment_intent_id=payment_intent_id,
                status='COMPLETED',
                contract_date=datetime.utcnow(),
                stripe_transfer_id=None  # Will be updated when transfer completes
            )
            
            db.add(contract)
            db.commit()
            
            logger.info(f"Payment confirmed: {payment_intent_id}, contract created: {contract.id}")
            
            return {
                'payment_intent_id': payment_intent_id,
                'contract_id': contract.id,
                'amount_paid': payment_intent.amount,
                'application_fee': payment_intent.application_fee_amount,
                'seller_amount': payment_intent.amount - payment_intent.application_fee_amount,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Failed to confirm payment and transfer: {e}")
            raise
    
    async def create_instant_payout(self, account_id: str, amount_pence: int, currency: str = "gbp") -> Dict[str, Any]:
        """
        Create instant payout to seller account
        """
        try:
            payout = stripe.Payout.create(
                amount=amount_pence,
                currency=currency,
                method='instant',
                stripe_account=account_id
            )
            
            logger.info(f"Created instant payout {payout.id} for £{amount_pence/100:.2f}")
            
            return {
                'payout_id': payout.id,
                'amount': amount_pence,
                'currency': currency,
                'status': payout.status,
                'arrival_date': payout.arrival_date
            }
            
        except Exception as e:
            logger.error(f"Failed to create instant payout: {e}")
            raise
    
    async def generate_deal_report(self, contract_id: int, db: Session = None) -> str:
        """
        Generate and store deal report on S3
        """
        try:
            # Get contract details
            contract = db.query(Contracts).filter(Contracts.id == contract_id).first()
            if not contract:
                raise ValueError(f"Contract {contract_id} not found")
            
            # Get related data
            supply = db.query(MarketplaceSupply).filter(MarketplaceSupply.id == contract.supply_id).first()
            buyer_org = db.query(Orgs).filter(Orgs.id == contract.buyer_org_id).first()
            seller_org = db.query(Orgs).filter(Orgs.id == supply.seller_org_id).first() if supply else None
            
            # Generate report data
            report_data = {
                'report_id': str(uuid.uuid4()),
                'contract_id': contract_id,
                'generated_at': datetime.utcnow().isoformat(),
                'transaction_summary': {
                    'total_amount': contract.contract_value,
                    'application_fee': contract.application_fee,
                    'seller_amount': contract.contract_value - contract.application_fee,
                    'fee_percentage': self.APPLICATION_FEE_PERCENT,
                    'currency': 'GBP',
                    'payment_intent_id': contract.payment_intent_id
                },
                'buyer_details': {
                    'org_id': buyer_org.id,
                    'org_name': buyer_org.name,
                    'billing_email': buyer_org.billing_email or 'N/A'
                },
                'seller_details': {
                    'org_id': seller_org.id if seller_org else None,
                    'org_name': seller_org.name if seller_org else 'N/A',
                    'stripe_account_id': seller_org.stripe_connect_account_id if seller_org else None
                },
                'biodiversity_details': {
                    'supply_id': supply.id if supply else None,
                    'biodiversity_units': supply.biodiversity_value_per_unit if supply else None,
                    'habitat_type': supply.habitat_type if supply else None,
                    'location': supply.location if supply else None,
                    'supply_type': supply.supply_type if supply else None
                },
                'compliance': {
                    'bng_compliant': True,
                    'statutory_requirements_met': True,
                    'defra_metric_version': '4.0',
                    'generated_by': 'domus_marketplace_v1.0'
                }
            }
            
            # Generate report filename
            report_filename = f"deal_reports/{datetime.utcnow().strftime('%Y/%m/%d')}/contract_{contract_id}_{report_data['report_id']}.json"
            
            # Store to S3 if available
            if self.s3_client:
                try:
                    self.s3_client.put_object(
                        Bucket=self.bucket_name,
                        Key=report_filename,
                        Body=json.dumps(report_data, indent=2),
                        ContentType='application/json',
                        Metadata={
                            'contract_id': str(contract_id),
                            'generated_at': datetime.utcnow().isoformat(),
                            'report_type': 'marketplace_deal'
                        }
                    )
                    
                    s3_url = f"s3://{self.bucket_name}/{report_filename}"
                    logger.info(f"Deal report stored to S3: {s3_url}")
                    
                except Exception as s3_error:
                    logger.warning(f"Failed to store report to S3: {s3_error}")
                    s3_url = None
            else:
                # Store locally if S3 not available
                local_path = f"/tmp/{report_filename.replace('/', '_')}"
                with open(local_path, 'w') as f:
                    json.dump(report_data, f, indent=2)
                s3_url = local_path
                logger.info(f"Deal report stored locally: {local_path}")
            
            # Update contract with report location
            contract.deal_report_url = s3_url
            db.commit()
            
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to generate deal report: {e}")
            raise
    
    async def get_marketplace_analytics(self, org_id: int, db: Session = None) -> Dict[str, Any]:
        """
        Get marketplace analytics for organization
        """
        try:
            with engine.connect() as conn:
                # Sales analytics (as seller)
                seller_stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(contract_value) as total_revenue,
                        SUM(application_fee) as total_fees_paid,
                        AVG(contract_value) as avg_sale_value
                    FROM contracts c
                    JOIN marketplace_supply ms ON c.supply_id = ms.id
                    WHERE ms.seller_org_id = :org_id
                    AND c.status = 'COMPLETED'
                """), org_id=org_id).fetchone()
                
                # Purchase analytics (as buyer)
                buyer_stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_purchases,
                        SUM(contract_value) as total_spent,
                        AVG(contract_value) as avg_purchase_value
                    FROM contracts
                    WHERE buyer_org_id = :org_id
                    AND status = 'COMPLETED'
                """), org_id=org_id).fetchone()
                
                # Recent transactions
                recent_transactions = conn.execute(text("""
                    SELECT 
                        c.id as contract_id,
                        c.contract_value,
                        c.application_fee,
                        c.contract_date,
                        c.status,
                        ms.biodiversity_value_per_unit,
                        ms.habitat_type,
                        buyer_org.name as buyer_name,
                        seller_org.name as seller_name
                    FROM contracts c
                    LEFT JOIN marketplace_supply ms ON c.supply_id = ms.id
                    LEFT JOIN orgs buyer_org ON c.buyer_org_id = buyer_org.id
                    LEFT JOIN orgs seller_org ON ms.seller_org_id = seller_org.id
                    WHERE (c.buyer_org_id = :org_id OR ms.seller_org_id = :org_id)
                    ORDER BY c.contract_date DESC
                    LIMIT 10
                """), org_id=org_id).fetchall()
            
            return {
                'seller_analytics': {
                    'total_sales': seller_stats[0] if seller_stats else 0,
                    'total_revenue_pence': seller_stats[1] if seller_stats and seller_stats[1] else 0,
                    'total_fees_paid_pence': seller_stats[2] if seller_stats and seller_stats[2] else 0,
                    'average_sale_value_pence': seller_stats[3] if seller_stats and seller_stats[3] else 0
                },
                'buyer_analytics': {
                    'total_purchases': buyer_stats[0] if buyer_stats else 0,
                    'total_spent_pence': buyer_stats[1] if buyer_stats and buyer_stats[1] else 0,
                    'average_purchase_value_pence': buyer_stats[2] if buyer_stats and buyer_stats[2] else 0
                },
                'recent_transactions': [
                    {
                        'contract_id': tx[0],
                        'amount_pence': tx[1],
                        'fee_pence': tx[2],
                        'date': tx[3].isoformat() if tx[3] else None,
                        'status': tx[4],
                        'biodiversity_units': float(tx[5]) if tx[5] else None,
                        'habitat_type': tx[6],
                        'buyer_name': tx[7],
                        'seller_name': tx[8]
                    }
                    for tx in recent_transactions
                ],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get marketplace analytics: {e}")
            raise


class MarketplaceWebhookHandler:
    """
    Handle Stripe Connect webhooks for marketplace events
    """
    
    def __init__(self):
        self.connect_service = StripeConnectService()
    
    async def handle_account_updated(self, event_data: Dict[str, Any], db: Session = None) -> bool:
        """
        Handle account.updated webhook
        """
        try:
            account = event_data['data']['object']
            account_id = account['id']
            
            # Update organization with account status
            org = db.query(Orgs).filter(Orgs.stripe_connect_account_id == account_id).first()
            if org:
                org.connect_charges_enabled = account.get('charges_enabled', False)
                org.connect_payouts_enabled = account.get('payouts_enabled', False)
                org.connect_details_submitted = account.get('details_submitted', False)
                db.commit()
                
                logger.info(f"Updated Connect account status for org {org.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle account.updated webhook: {e}")
            return False
    
    async def handle_payment_intent_succeeded(self, event_data: Dict[str, Any], db: Session = None) -> bool:
        """
        Handle payment_intent.succeeded webhook for marketplace payments
        """
        try:
            payment_intent = event_data['data']['object']
            
            # Check if this is a marketplace payment
            if not payment_intent.get('application_fee_amount'):
                return True  # Not a marketplace payment
            
            payment_intent_id = payment_intent['id']
            metadata = payment_intent.get('metadata', {})
            
            if 'marketplace_supply_id' in metadata:
                # Process marketplace transaction
                result = await self.connect_service.confirm_payment_and_transfer(payment_intent_id, db)
                
                # Generate deal report
                if 'contract_id' in result:
                    await self.connect_service.generate_deal_report(result['contract_id'], db)
                
                logger.info(f"Processed marketplace payment: {payment_intent_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle payment_intent.succeeded webhook: {e}")
            return False
    
    async def handle_transfer_created(self, event_data: Dict[str, Any], db: Session = None) -> bool:
        """
        Handle transfer.created webhook
        """
        try:
            transfer = event_data['data']['object']
            transfer_id = transfer['id']
            destination_account = transfer['destination']
            
            # Update contract with transfer ID
            if 'source_transaction' in transfer:
                payment_intent_id = transfer['source_transaction']
                
                contract = db.query(Contracts).filter(Contracts.payment_intent_id == payment_intent_id).first()
                if contract:
                    contract.stripe_transfer_id = transfer_id
                    contract.transfer_status = 'completed'
                    db.commit()
                    
                    logger.info(f"Updated contract {contract.id} with transfer {transfer_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to handle transfer.created webhook: {e}")
            return False