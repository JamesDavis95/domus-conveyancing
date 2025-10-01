"""
Client Onboarding System
Complete onboarding flow with account setup, subscription selection, payment processing, and user activation
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models import get_db, User, Organization, Base
from production_auth_complete import AuthService, get_current_user
from stripe_integration_complete import StripeService, BillingAPI
from backend_auth_complete import UserRole, PlanType, PLAN_PRICING, PLAN_LIMITS
from production_data_layer import NotificationService, NotificationType
import uuid
from enum import Enum as PyEnum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import logging

logger = logging.getLogger(__name__)

class OnboardingStep(PyEnum):
    REGISTRATION = "registration"
    PLAN_SELECTION = "plan_selection" 
    PAYMENT_SETUP = "payment_setup"
    PROFILE_COMPLETION = "profile_completion"
    TUTORIAL = "tutorial"
    COMPLETED = "completed"

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_step = Column(Enum(OnboardingStep), default=OnboardingStep.REGISTRATION)
    completed_steps = Column(Text)  # JSON list of completed steps
    
    # Registration data
    registration_data = Column(Text)  # JSON
    selected_plan = Column(Enum(PlanType))
    stripe_setup_intent_id = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Marketing attribution
    referral_source = Column(String)
    utm_campaign = Column(String)
    utm_source = Column(String)
    utm_medium = Column(String)

class EmailService:
    """Email service for onboarding communications"""
    
    @staticmethod
    async def send_welcome_email(user: User, organization: Organization) -> bool:
        """Send welcome email to new user"""
        try:
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', 'hello@domusplanning.co.uk')
            smtp_password = os.getenv('SMTP_PASSWORD', 'your-app-password')
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = user.email
            msg['Subject'] = f"Welcome to Domus Planning Platform, {user.name}!"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                    .content {{ background: white; padding: 30px; }}
                    .button {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
                    .features {{ background: #f8fafc; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                    .feature {{ margin: 10px 0; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to Domus Planning Platform!</h1>
                        <p>Your professional planning intelligence system is ready</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user.name},</h2>
                        
                        <p>Congratulations on joining Domus Planning Platform! Your account for <strong>{organization.name}</strong> has been successfully created.</p>
                        
                        <p>You now have access to our complete AI-powered planning intelligence system:</p>
                        
                        <div class="features">
                            <div class="feature">
                                <strong>🎯 Planning AI</strong> - Site analysis with approval probability prediction
                            </div>
                            <div class="feature">
                                <strong>📋 Auto-Docs</strong> - Professional planning document generation
                            </div>
                            <div class="feature">
                                <strong>🏠 Property API</strong> - Unified UK property data integration
                            </div>
                            <div class="feature">
                                <strong>🌱 BNG Marketplace</strong> - Biodiversity Net Gain trading platform
                            </div>
                        </div>
                        
                        <p><strong>Your Plan:</strong> {organization.plan_type.value.title()} Plan</p>
                        <p><strong>Trial Period:</strong> 14 days free (until {organization.trial_end.strftime('%B %d, %Y') if organization.trial_end else 'N/A'})</p>
                        
                        <a href="https://domus-conveyancing.onrender.com" class="button">Launch Platform</a>
                        
                        <h3>Getting Started</h3>
                        <ol>
                            <li>Complete your onboarding tutorial</li>
                            <li>Run your first site analysis</li>
                            <li>Explore the BNG marketplace</li>
                            <li>Generate your first planning document</li>
                        </ol>
                        
                        <h3>Need Help?</h3>
                        <p>Our support team is here to help:</p>
                        <ul>
                            <li>📧 Email: support@domusplanning.co.uk</li>
                            <li>📚 Knowledge Base: <a href="https://docs.domusplanning.co.uk">docs.domusplanning.co.uk</a></li>
                            <li>💬 Live Chat: Available in your dashboard</li>
                        </ul>
                        
                        <p>Thank you for choosing Domus Planning Platform. We're excited to help you transform your planning workflow!</p>
                        
                        <p>Best regards,<br>
                        The Domus Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
            return False
    
    @staticmethod
    async def send_trial_reminder(user: User, days_remaining: int) -> bool:
        """Send trial reminder email"""
        try:
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', 'hello@domusplanning.co.uk')
            smtp_password = os.getenv('SMTP_PASSWORD', 'your-app-password')
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = user.email
            msg['Subject'] = f"Your Domus trial expires in {days_remaining} days"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
                    .content {{ background: white; padding: 30px; }}
                    .button {{ background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0; }}
                    .urgency {{ background: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Trial Reminder</h1>
                        <p>Don't lose access to your planning intelligence system</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user.name},</h2>
                        
                        <div class="urgency">
                            <strong>⏰ Your free trial expires in {days_remaining} days</strong>
                        </div>
                        
                        <p>We hope you've been enjoying the Domus Planning Platform! Your trial period is ending soon, and we don't want you to lose access to:</p>
                        
                        <ul>
                            <li>AI-powered site analysis and approval predictions</li>
                            <li>Professional planning document generation</li>
                            <li>Comprehensive UK property data access</li>
                            <li>BNG marketplace for biodiversity offsetting</li>
                        </ul>
                        
                        <p><strong>Continue your subscription to maintain uninterrupted access.</strong></p>
                        
                        <a href="https://domus-conveyancing.onrender.com/billing" class="button">Update Billing</a>
                        
                        <p>Questions? Our team is here to help at support@domusplanning.co.uk</p>
                        
                        <p>Best regards,<br>
                        The Domus Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send trial reminder: {str(e)}")
            return False

class OnboardingService:
    """Complete onboarding workflow service"""
    
    @staticmethod
    async def start_onboarding(
        email: str,
        referral_source: Optional[str] = None,
        utm_params: Optional[Dict[str, str]] = None,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Start onboarding process"""
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create onboarding session
        session = OnboardingSession(
            referral_source=referral_source,
            utm_campaign=utm_params.get('utm_campaign') if utm_params else None,
            utm_source=utm_params.get('utm_source') if utm_params else None,
            utm_medium=utm_params.get('utm_medium') if utm_params else None
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return {
            "onboarding_session_id": session.id,
            "current_step": session.current_step.value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def complete_registration(
        session_id: str,
        registration_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Complete user registration step"""
        
        session = db.query(OnboardingSession).filter(OnboardingSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # Create user and organization
        user = await AuthService.create_user(
            email=registration_data["email"],
            password=registration_data["password"],
            name=registration_data["name"],
            role=UserRole(registration_data.get("role", "developer")),
            organization_name=registration_data["organization_name"],
            plan_type=PlanType.CORE,  # Default to core plan
            db=db
        )
        
        # Update onboarding session
        session.user_id = user.id
        session.registration_data = json.dumps(registration_data)
        session.current_step = OnboardingStep.PLAN_SELECTION
        session.completed_steps = json.dumps([OnboardingStep.REGISTRATION.value])
        db.commit()
        
        return {
            "user_id": user.id,
            "next_step": session.current_step.value,
            "access_token": AuthService.create_access_token({
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value,
                "org_id": user.org_id
            })
        }
    
    @staticmethod
    async def select_plan(
        session_id: str,
        plan_type: PlanType,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Handle plan selection step"""
        
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == session_id,
            OnboardingSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # Update organization plan
        user.organization.plan_type = plan_type
        
        # Update onboarding session
        session.selected_plan = plan_type
        session.current_step = OnboardingStep.PAYMENT_SETUP
        
        completed_steps = json.loads(session.completed_steps or "[]")
        completed_steps.append(OnboardingStep.PLAN_SELECTION.value)
        session.completed_steps = json.dumps(completed_steps)
        
        db.commit()
        
        # Create Stripe setup intent for payment method
        setup_intent = await StripeService.create_setup_intent(user.organization.stripe_customer_id)
        session.stripe_setup_intent_id = setup_intent["setup_intent_id"]
        db.commit()
        
        return {
            "selected_plan": plan_type.value,
            "plan_pricing": PLAN_PRICING[plan_type],
            "setup_intent_client_secret": setup_intent["client_secret"],
            "next_step": session.current_step.value
        }
    
    @staticmethod
    async def complete_payment_setup(
        session_id: str,
        payment_method_id: str,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Complete payment setup step"""
        
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == session_id,
            OnboardingSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # Create subscription if not trial period
        if session.selected_plan and session.selected_plan != PlanType.CORE:
            subscription_data = await StripeService.create_subscription(
                user.organization.stripe_customer_id,
                session.selected_plan,
                trial_days=14
            )
        
        # Update onboarding session
        session.current_step = OnboardingStep.PROFILE_COMPLETION
        completed_steps = json.loads(session.completed_steps or "[]")
        completed_steps.append(OnboardingStep.PAYMENT_SETUP.value)
        session.completed_steps = json.dumps(completed_steps)
        
        db.commit()
        
        return {
            "payment_setup": "completed",
            "subscription_status": "active_trial",
            "next_step": session.current_step.value
        }
    
    @staticmethod
    async def complete_profile(
        session_id: str,
        profile_data: Dict[str, Any],
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Complete profile setup step"""
        
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == session_id,
            OnboardingSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # Update user profile with additional information
        # This could include company details, preferences, etc.
        
        # Update onboarding session
        session.current_step = OnboardingStep.TUTORIAL
        completed_steps = json.loads(session.completed_steps or "[]")
        completed_steps.append(OnboardingStep.PROFILE_COMPLETION.value)
        session.completed_steps = json.dumps(completed_steps)
        
        db.commit()
        
        return {
            "profile_completed": True,
            "next_step": session.current_step.value
        }
    
    @staticmethod
    async def complete_tutorial(
        session_id: str,
        user: User,
        background_tasks: BackgroundTasks,
        db: Session
    ) -> Dict[str, Any]:
        """Complete tutorial and onboarding"""
        
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == session_id,
            OnboardingSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        # Complete onboarding
        session.current_step = OnboardingStep.COMPLETED
        session.completed_at = datetime.utcnow()
        
        completed_steps = json.loads(session.completed_steps or "[]")
        completed_steps.extend([OnboardingStep.TUTORIAL.value, OnboardingStep.COMPLETED.value])
        session.completed_steps = json.dumps(completed_steps)
        
        db.commit()
        
        # Send welcome email
        background_tasks.add_task(EmailService.send_welcome_email, user, user.organization)
        
        # Create welcome notification
        await NotificationService.create_notification(
            user.id,
            NotificationType.SYSTEM_ALERT,
            "Welcome to Domus Planning Platform!",
            "Your account is ready. Start by analyzing your first site or exploring the BNG marketplace.",
            priority="normal",
            db=db
        )
        
        return {
            "onboarding_completed": True,
            "welcome_message": f"Welcome to Domus Planning Platform, {user.name}! Your account is ready.",
            "next_steps": [
                "Run your first site analysis",
                "Explore the BNG marketplace", 
                "Generate planning documents",
                "Set up team members"
            ]
        }
    
    @staticmethod
    async def get_onboarding_status(
        session_id: str,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Get current onboarding status"""
        
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == session_id,
            OnboardingSession.user_id == user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Onboarding session not found")
        
        completed_steps = json.loads(session.completed_steps or "[]")
        
        return {
            "session_id": session.id,
            "current_step": session.current_step.value,
            "completed_steps": completed_steps,
            "progress_percentage": (len(completed_steps) / len(OnboardingStep)) * 100,
            "selected_plan": session.selected_plan.value if session.selected_plan else None,
            "created_at": session.created_at.isoformat()
        }

class OnboardingAPI:
    """Onboarding API endpoints"""
    
    @staticmethod
    async def start_registration(
        email: str,
        referral_source: Optional[str] = None,
        utm_campaign: Optional[str] = None,
        utm_source: Optional[str] = None,
        utm_medium: Optional[str] = None,
        db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Start registration process"""
        
        utm_params = {
            "utm_campaign": utm_campaign,
            "utm_source": utm_source,
            "utm_medium": utm_medium
        } if any([utm_campaign, utm_source, utm_medium]) else None
        
        result = await OnboardingService.start_onboarding(
            email=email,
            referral_source=referral_source,
            utm_params=utm_params,
            db=db
        )
        
        return result
    
    @staticmethod
    async def get_plan_options() -> Dict[str, Any]:
        """Get available plan options"""
        
        return {
            "plans": [
                {
                    "type": plan_type.value,
                    "name": config["name"],
                    "description": config["description"],
                    "price": config["amount"] / 100,  # Convert from pence
                    "currency": config["currency"],
                    "interval": config["interval"],
                    "features": {
                        "site_analyses": PLAN_LIMITS[plan_type]["site_analyses"],
                        "documents": PLAN_LIMITS[plan_type]["documents"],
                        "api_calls": PLAN_LIMITS[plan_type]["api_calls"],
                        "bng_listings": PLAN_LIMITS[plan_type]["bng_listings"],
                        "users": PLAN_LIMITS[plan_type]["users"]
                    }
                }
                for plan_type, config in PLAN_PRICING.items()
            ]
        }

# Background task for trial reminders
async def send_trial_reminders():
    """Send trial reminder emails"""
    db = next(get_db())
    
    # Find organizations with trials ending soon
    three_days_from_now = datetime.utcnow() + timedelta(days=3)
    one_day_from_now = datetime.utcnow() + timedelta(days=1)
    
    # 3-day reminder
    orgs_3_days = db.query(Organization).filter(
        Organization.trial_end <= three_days_from_now,
        Organization.trial_end > datetime.utcnow(),
        Organization.subscription_status == "trialing"
    ).all()
    
    for org in orgs_3_days:
        user = db.query(User).filter(User.org_id == org.id).first()
        if user:
            await EmailService.send_trial_reminder(user, 3)
    
    # 1-day reminder
    orgs_1_day = db.query(Organization).filter(
        Organization.trial_end <= one_day_from_now,
        Organization.trial_end > datetime.utcnow(),
        Organization.subscription_status == "trialing"
    ).all()
    
    for org in orgs_1_day:
        user = db.query(User).filter(User.org_id == org.id).first()
        if user:
            await EmailService.send_trial_reminder(user, 1)
    
    db.close()