"""
Communications Module for LA System
Handles email notifications, SMS, and applicant communications
"""
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
import os
from jinja2 import Template

logger = logging.getLogger(__name__)

class CommunicationsEngine:
    """Handles all communications for LA matters"""
    
    def __init__(self):
        # Email configuration
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@council.gov.uk")
        
        # Template directory
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load email templates"""
        return {
            "application_received": """
Dear {{ applicant_name }},

Thank you for your Local Land Charges search application.

Application Reference: {{ matter_ref }}
Property Address: {{ address }}
Products Requested: {{ products }}
Fee: £{{ fee }}

Your application has been received and is being processed. You will receive updates by email as your search progresses.

Expected completion: {{ due_date }}
Status tracking: {{ portal_url }}

Kind regards,
{{ council_name }} Local Land Charges Team
            """,
            
            "payment_confirmation": """
Dear {{ applicant_name }},

Payment Confirmed - {{ matter_ref }}

We have received your payment of £{{ amount }} for your Local Land Charges search.

Your application is now being processed and you will receive the results by {{ due_date }}.

You can track progress at: {{ portal_url }}

Kind regards,
{{ council_name }} Local Land Charges Team
            """,
            
            "search_in_progress": """
Dear {{ applicant_name }},

Search Update - {{ matter_ref }}

Your Local Land Charges search is currently being processed by our team.

Status: {{ status }}
Expected completion: {{ due_date }}

You will be notified as soon as your search results are ready.

Kind regards,
{{ council_name }} Local Land Charges Team
            """,
            
            "search_ready": """
Dear {{ applicant_name }},

Search Results Ready - {{ matter_ref }}

Your Local Land Charges search has been completed and is ready for download.

Download your results: {{ download_url }}
Valid until: {{ expiry_date }}

Results include:
{{ results_summary }}

If you have any questions about your search results, please contact us.

Kind regards,
{{ council_name }} Local Land Charges Team
            """,
            
            "sla_reminder_internal": """
Subject: SLA Reminder - {{ matter_ref }}

Matter {{ matter_ref }} is due in {{ days_remaining }} working days.

Property: {{ address }}
Due Date: {{ due_date }}
Assigned to: {{ assigned_to }}
Current Status: {{ status }}

Please ensure this matter is completed on time.

{{ dashboard_url }}
            """,
            
            "qa_review_required": """
Subject: QA Review Required - {{ matter_ref }}

A matter has been completed and requires quality assurance review.

Matter: {{ matter_ref }}
Property: {{ address }}
Caseworker: {{ caseworker }}
Review Type: {{ review_type }}
Findings: {{ findings_count }}

Please complete the review: {{ review_url }}
            """
        }
    
    async def send_application_received_email(self, matter_data: Dict[str, Any]) -> bool:
        """Send application received confirmation"""
        try:
            template = Template(self.templates["application_received"])
            
            products = []
            if matter_data.get("llc1_requested") == "true":
                products.append("LLC1")
            if matter_data.get("con29_requested") == "true":
                products.append("CON29")
            if matter_data.get("con29o_requested") == "true":
                products.append("CON29O")
            
            content = template.render(
                applicant_name=matter_data.get("applicant_name", "Applicant"),
                matter_ref=matter_data.get("ref", ""),
                address=matter_data.get("address", ""),
                products=", ".join(products),
                fee=matter_data.get("fee_calculated", 0),
                due_date=matter_data.get("sla_due_date", "").split("T")[0] if matter_data.get("sla_due_date") else "TBC",
                portal_url="https://portal.council.gov.uk/track",
                council_name="Local Authority"
            )
            
            return await self._send_email(
                to_email=matter_data.get("applicant_email", ""),
                subject=f"Application Received - {matter_data.get('ref', '')}",
                content=content
            )
            
        except Exception as e:
            logger.error(f"Application received email failed: {e}")
            return False
    
    async def send_payment_confirmation_email(self, matter_data: Dict[str, Any], payment_data: Dict[str, Any]) -> bool:
        """Send payment confirmation email"""
        try:
            template = Template(self.templates["payment_confirmation"])
            
            content = template.render(
                applicant_name=matter_data.get("applicant_name", "Applicant"),
                matter_ref=matter_data.get("ref", ""),
                amount=payment_data.get("amount", 0),
                due_date=matter_data.get("sla_due_date", "").split("T")[0] if matter_data.get("sla_due_date") else "TBC",
                portal_url="https://portal.council.gov.uk/track",
                council_name="Local Authority"
            )
            
            return await self._send_email(
                to_email=matter_data.get("applicant_email", ""),
                subject=f"Payment Confirmed - {matter_data.get('ref', '')}",
                content=content
            )
            
        except Exception as e:
            logger.error(f"Payment confirmation email failed: {e}")
            return False
    
    async def send_search_ready_email(self, matter_data: Dict[str, Any], results_summary: str) -> bool:
        """Send search results ready notification"""
        try:
            template = Template(self.templates["search_ready"])
            
            download_url = f"https://portal.council.gov.uk/download/{matter_data.get('id', '')}"
            expiry_date = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
            
            content = template.render(
                applicant_name=matter_data.get("applicant_name", "Applicant"),
                matter_ref=matter_data.get("ref", ""),
                download_url=download_url,
                expiry_date=expiry_date,
                results_summary=results_summary,
                council_name="Local Authority"
            )
            
            return await self._send_email(
                to_email=matter_data.get("applicant_email", ""),
                subject=f"Search Results Ready - {matter_data.get('ref', '')}",
                content=content
            )
            
        except Exception as e:
            logger.error(f"Search ready email failed: {e}")
            return False
    
    async def send_sla_reminder_internal(self, matter_data: Dict[str, Any], staff_email: str, days_remaining: int) -> bool:
        """Send SLA reminder to staff"""
        try:
            template = Template(self.templates["sla_reminder_internal"])
            
            content = template.render(
                matter_ref=matter_data.get("ref", ""),
                address=matter_data.get("address", ""),
                days_remaining=days_remaining,
                due_date=matter_data.get("sla_due_date", "").split("T")[0] if matter_data.get("sla_due_date") else "TBC",
                assigned_to=matter_data.get("assigned_to", "Unassigned"),
                status=matter_data.get("status", ""),
                dashboard_url="https://portal.council.gov.uk/dashboard"
            )
            
            return await self._send_email(
                to_email=staff_email,
                subject=f"SLA Reminder - {matter_data.get('ref', '')}",
                content=content
            )
            
        except Exception as e:
            logger.error(f"SLA reminder email failed: {e}")
            return False
    
    async def send_qa_review_notification(self, matter_data: Dict[str, Any], reviewer_email: str, review_data: Dict[str, Any]) -> bool:
        """Send QA review notification to reviewer"""
        try:
            template = Template(self.templates["qa_review_required"])
            
            content = template.render(
                matter_ref=matter_data.get("ref", ""),
                address=matter_data.get("address", ""),
                caseworker=matter_data.get("assigned_to", "Unknown"),
                review_type=review_data.get("review_type", "standard"),
                findings_count=review_data.get("findings_count", 0),
                review_url=f"https://portal.council.gov.uk/qa/{review_data.get('review_id', '')}"
            )
            
            return await self._send_email(
                to_email=reviewer_email,
                subject=f"QA Review Required - {matter_data.get('ref', '')}",
                content=content
            )
            
        except Exception as e:
            logger.error(f"QA review notification failed: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email via SMTP"""
        try:
            if not to_email:
                logger.warning("No recipient email address provided")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(content, 'plain'))
            
            # Send via SMTP
            if self.smtp_host == "localhost":
                # Development mode - just log
                logger.info(f"EMAIL (dev): To={to_email}, Subject={subject}")
                logger.debug(f"Content: {content}")
                return True
            else:
                # Production mode - send via SMTP
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    if self.smtp_user:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
                
                logger.info(f"Email sent to {to_email}: {subject}")
                return True
                
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False
    
    async def log_communication(self, matter_id: str, comm_type: str, direction: str, recipient: str, content: str, db) -> bool:
        """Log communication in database"""
        try:
            from la.models import LACommunication
            
            communication = LACommunication(
                matter_id=matter_id,
                communication_type=comm_type,
                direction=direction,
                recipient=recipient,
                content=content,
                delivery_status="sent"
            )
            
            db.add(communication)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Communication logging failed: {e}")
            return False
    
    async def get_communication_history(self, matter_id: str, db) -> List[Dict[str, Any]]:
        """Get communication history for a matter"""
        try:
            from la.models import LACommunication
            
            communications = db.query(LACommunication).filter(
                LACommunication.matter_id == matter_id
            ).order_by(LACommunication.created_at.desc()).all()
            
            return [
                {
                    "id": comm.id,
                    "type": comm.communication_type,
                    "direction": comm.direction,
                    "recipient": comm.recipient,
                    "subject": comm.subject,
                    "status": comm.delivery_status,
                    "created_at": comm.created_at.isoformat()
                }
                for comm in communications
            ]
            
        except Exception as e:
            logger.error(f"Communication history query failed: {e}")
            return []

# Global communications engine
communications = CommunicationsEngine()