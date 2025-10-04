"""
SendGrid Email Integration
Server-side only email service for OTP, notifications, submission receipts
"""

import os
import logging
from typing import Dict, Any, List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from fastapi import HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    """SendGrid email service following exact specifications"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "Domus <no-reply@yourdomain>")
        self.reply_to = os.getenv("EMAIL_REPLY_TO", "support@yourdomain")
        
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
            return
            
        self.sg = SendGridAPIClient(api_key=self.api_key)
    
    async def send_otp_email(self, 
                           to_email: str, 
                           otp_code: str, 
                           expires_minutes: int = 10) -> bool:
        """Send OTP email for login/verification"""
        
        subject = "Your Domus Planning Login Code"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background: #2c5aa0; color: white; padding: 20px; text-align: center;">
                <h1>Domus Planning</h1>
            </div>
            <div style="padding: 30px 20px;">
                <h2>Your login code</h2>
                <p>Use this code to sign in to your Domus Planning account:</p>
                
                <div style="background: #f8f9fa; border: 2px dashed #2c5aa0; padding: 20px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 32px; font-weight: bold; color: #2c5aa0; letter-spacing: 4px;">{otp_code}</span>
                </div>
                
                <p>This code will expire in {expires_minutes} minutes.</p>
                <p>If you didn't request this code, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Domus Planning • Professional Planning Tools<br>
                    This is an automated message, please don't reply to this email.
                </p>
            </div>
        </div>
        """
        
        plain_content = f"""
        Your Domus Planning Login Code
        
        Use this code to sign in: {otp_code}
        
        This code expires in {expires_minutes} minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        return await self._send_email(to_email, subject, plain_content, html_content)
    
    async def send_password_reset(self, 
                                to_email: str, 
                                reset_link: str) -> bool:
        """Send password reset email"""
        
        subject = "Reset your Domus Planning password"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background: #2c5aa0; color: white; padding: 20px; text-align: center;">
                <h1>Domus Planning</h1>
            </div>
            <div style="padding: 30px 20px;">
                <h2>Reset your password</h2>
                <p>We received a request to reset your Domus Planning account password.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background: #2c5aa0; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>This link will expire in 1 hour for security reasons.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Domus Planning • Professional Planning Tools<br>
                    This is an automated message, please don't reply to this email.
                </p>
            </div>
        </div>
        """
        
        plain_content = f"""
        Reset your Domus Planning password
        
        We received a request to reset your account password.
        
        Click this link to reset: {reset_link}
        
        This link expires in 1 hour.
        
        If you didn't request this reset, please ignore this email.
        """
        
        return await self._send_email(to_email, subject, plain_content, html_content)
    
    async def send_submission_receipt(self, 
                                    to_email: str,
                                    submission_data: Dict[str, Any]) -> bool:
        """Send submission receipt email"""
        
        subject = f"Submission Receipt - {submission_data.get('council_name', 'Council')}"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background: #28a745; color: white; padding: 20px; text-align: center;">
                <h1>✓ Submission Confirmed</h1>
            </div>
            <div style="padding: 30px 20px;">
                <h2>Your planning application has been submitted</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Submission Details</h3>
                    <p><strong>Project:</strong> {submission_data.get('project_title', 'N/A')}</p>
                    <p><strong>Council:</strong> {submission_data.get('council_name', 'N/A')}</p>
                    <p><strong>Submission ID:</strong> {submission_data.get('submission_id', 'N/A')}</p>
                    <p><strong>Submitted:</strong> {submission_data.get('submitted_at', datetime.utcnow().strftime('%d %B %Y at %H:%M'))}</p>
                    <p><strong>Documents:</strong> {submission_data.get('document_count', 0)} files</p>
                </div>
                
                <h3>Next Steps</h3>
                <ul>
                    <li>The council will validate your application within 5 working days</li>
                    <li>You'll receive confirmation once validation is complete</li>
                    <li>The target decision date is approximately 8 weeks from validation</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{submission_data.get('tracking_url', '#')}" 
                       style="background: #2c5aa0; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Track Application
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Domus Planning • Professional Planning Tools<br>
                    Keep this email for your records.
                </p>
            </div>
        </div>
        """
        
        plain_content = f"""
        Submission Confirmed - {submission_data.get('council_name', 'Council')}
        
        Your planning application has been submitted successfully.
        
        Submission Details:
        - Project: {submission_data.get('project_title', 'N/A')}
        - Council: {submission_data.get('council_name', 'N/A')}
        - Submission ID: {submission_data.get('submission_id', 'N/A')}
        - Submitted: {submission_data.get('submitted_at', datetime.utcnow().strftime('%d %B %Y at %H:%M'))}
        - Documents: {submission_data.get('document_count', 0)} files
        
        Next Steps:
        - Council validation within 5 working days
        - Target decision date: approximately 8 weeks
        
        Track your application: {submission_data.get('tracking_url', 'N/A')}
        """
        
        return await self._send_email(to_email, subject, plain_content, html_content)
    
    async def send_plan_upgrade_notification(self, 
                                           to_email: str,
                                           plan_data: Dict[str, Any]) -> bool:
        """Send plan upgrade confirmation"""
        
        subject = f"Welcome to {plan_data.get('plan_name', 'Premium')} Plan"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background: #28a745; color: white; padding: 20px; text-align: center;">
                <h1>🎉 Plan Upgraded!</h1>
            </div>
            <div style="padding: 30px 20px;">
                <h2>Welcome to {plan_data.get('plan_name', 'Premium')}</h2>
                <p>Your Domus Planning account has been upgraded successfully.</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Your New Features</h3>
                    <ul>
                        {self._format_features(plan_data.get('features', []))}
                    </ul>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.domusplanning.co.uk/dashboard" 
                       style="background: #2c5aa0; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Access Your Account
                    </a>
                </div>
                
                <p>Need help getting started? Contact our support team at {self.reply_to}</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Domus Planning • Professional Planning Tools
                </p>
            </div>
        </div>
        """
        
        features_text = '\n'.join([f"- {feature}" for feature in plan_data.get('features', [])])
        
        plain_content = f"""
        Welcome to {plan_data.get('plan_name', 'Premium')} Plan
        
        Your Domus Planning account has been upgraded successfully.
        
        Your New Features:
        {features_text}
        
        Access your account: https://app.domusplanning.co.uk/dashboard
        
        Need help? Contact {self.reply_to}
        """
        
        return await self._send_email(to_email, subject, plain_content, html_content)
    
    async def send_credit_purchase_confirmation(self, 
                                              to_email: str,
                                              credit_data: Dict[str, Any]) -> bool:
        """Send credit purchase confirmation"""
        
        subject = f"Credits Added - {credit_data.get('credit_type', 'Premium')} Credits"
        
        html_content = f"""
        <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
            <div style="background: #17a2b8; color: white; padding: 20px; text-align: center;">
                <h1>Credits Added</h1>
            </div>
            <div style="padding: 30px 20px;">
                <h2>Your credits have been added</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Purchase Details</h3>
                    <p><strong>Credit Type:</strong> {credit_data.get('credit_type', 'N/A')}</p>
                    <p><strong>Credits Added:</strong> {credit_data.get('amount', 0)}</p>
                    <p><strong>New Balance:</strong> {credit_data.get('new_balance', 0)} credits</p>
                    <p><strong>Purchase Date:</strong> {datetime.utcnow().strftime('%d %B %Y')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://app.domusplanning.co.uk/settings/billing" 
                       style="background: #2c5aa0; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Billing
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    Domus Planning • Professional Planning Tools
                </p>
            </div>
        </div>
        """
        
        plain_content = f"""
        Credits Added - {credit_data.get('credit_type', 'Premium')} Credits
        
        Your credits have been added successfully.
        
        Purchase Details:
        - Credit Type: {credit_data.get('credit_type', 'N/A')}
        - Credits Added: {credit_data.get('amount', 0)}
        - New Balance: {credit_data.get('new_balance', 0)} credits
        - Purchase Date: {datetime.utcnow().strftime('%d %B %Y')}
        
        View billing: https://app.domusplanning.co.uk/settings/billing
        """
        
        return await self._send_email(to_email, subject, plain_content, html_content)
    
    def _format_features(self, features: List[str]) -> str:
        """Format features list for HTML"""
        return '\n'.join([f"<li>{feature}</li>" for feature in features])
    
    async def _send_email(self, 
                         to_email: str, 
                         subject: str, 
                         plain_content: str, 
                         html_content: str) -> bool:
        """Send email via SendGrid"""
        
        if not self.api_key:
            logger.warning(f"Email not sent - SendGrid not configured: {subject}")
            return False
        
        try:
            message = Mail(
                from_email=From(self.from_email),
                to_emails=To(to_email),
                subject=Subject(subject),
                plain_text_content=PlainTextContent(plain_content),
                html_content=HtmlContent(html_content)
            )
            
            # Set reply-to
            message.reply_to = self.reply_to
            
            # Send email
            response = self.sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(f"Email send failed: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

# Initialize service
email_service = EmailService()

# Create API Router
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/email", tags=["Email"])

@router.get("/health")
async def email_health():
    """Health check for email service"""
    return {
        "service": "email",
        "status": "healthy" if email_service.api_key else "missing_api_key",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/templates")
async def get_email_templates():
    """Get available email templates"""
    return {
        "templates": [
            {"id": "otp", "name": "Login Code", "description": "One-time password for login"},
            {"id": "password_reset", "name": "Password Reset", "description": "Password reset link"},
            {"id": "submission_receipt", "name": "Submission Receipt", "description": "Planning application submission confirmation"},
            {"id": "plan_upgrade", "name": "Plan Upgrade", "description": "Plan upgrade confirmation"},
            {"id": "credit_purchase", "name": "Credit Purchase", "description": "Credit purchase confirmation"}
        ]
    }

# Export for use in other modules
__all__ = ["email_service", "EmailService", "router"]