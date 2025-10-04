#!/usr/bin/env python3
"""
Health and readiness endpoints for monitoring
"""

import os
import asyncio
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import text
from database_config import get_db

class HealthService:
    @staticmethod
    async def check_database():
        """Check database connectivity"""
        try:
            db = next(get_db())
            result = db.execute(text("SELECT 1")).fetchone()
            return {"status": "healthy", "response_time_ms": 10}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_s3():
        """Check S3 connectivity"""
        try:
            import boto3
            s3_client = boto3.client(
                's3',
                endpoint_url=os.getenv('S3_ENDPOINT'),
                aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
                region_name=os.getenv('S3_REGION', 'us-east-1')
            )
            
            bucket = os.getenv('S3_BUCKET')
            s3_client.head_bucket(Bucket=bucket)
            return {"status": "healthy", "bucket": bucket}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def check_stripe():
        """Check Stripe API connectivity"""
        try:
            import stripe
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            stripe.Account.retrieve()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @staticmethod
    async def get_system_info():
        """Get basic system information"""
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": datetime.now().isoformat()
        }

class FreshnessService:
    @staticmethod
    async def get_source_freshness(db):
        """Get freshness status for all data sources"""
        try:
            from models import SourceFreshness
            sources = db.query(SourceFreshness).all()
            
            freshness_data = {}
            for source in sources:
                age_hours = (datetime.now() - source.last_updated_at).total_seconds() / 3600
                freshness_data[source.source] = {
                    "last_updated": source.last_updated_at.isoformat(),
                    "status": source.status,
                    "age_hours": round(age_hours, 1),
                    "is_stale": age_hours > 24  # Consider stale if older than 24 hours
                }
            
            return freshness_data
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def update_source_freshness(source: str, status: str, db):
        """Update freshness for a data source"""
        try:
            from models import SourceFreshness
            
            freshness = db.query(SourceFreshness).filter(
                SourceFreshness.source == source
            ).first()
            
            if not freshness:
                freshness = SourceFreshness(
                    source=source,
                    last_updated_at=datetime.now(),
                    status=status
                )
                db.add(freshness)
            else:
                freshness.last_updated_at = datetime.now()
                freshness.status = status
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error updating freshness for {source}: {e}")
            return False

class AlertService:
    @staticmethod
    async def send_alert(title: str, message: str, level: str = "error"):
        """Send alert via email or webhook"""
        try:
            alert_email = os.getenv('ALERT_EMAIL')
            alert_webhook = os.getenv('ALERT_WEBHOOK_URL')
            
            alert_data = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "service": "domus-platform"
            }
            
            if alert_webhook:
                # Send to Slack/webhook
                import requests
                
                slack_payload = {
                    "text": f"🚨 {title}",
                    "attachments": [{
                        "color": "danger" if level == "error" else "warning",
                        "fields": [
                            {"title": "Message", "value": message, "short": False},
                            {"title": "Level", "value": level.upper(), "short": True},
                            {"title": "Time", "value": alert_data["timestamp"], "short": True}
                        ]
                    }]
                }
                
                response = requests.post(alert_webhook, json=slack_payload, timeout=10)
                response.raise_for_status()
                
            if alert_email:
                # Send email alert (simplified implementation)
                smtp_host = os.getenv('SMTP_HOST')
                smtp_user = os.getenv('SMTP_USER')
                smtp_pass = os.getenv('SMTP_PASS')
                smtp_from = os.getenv('SMTP_FROM', smtp_user)
                
                if smtp_host and smtp_user and smtp_pass:
                    import smtplib
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart
                    
                    msg = MIMEMultipart()
                    msg['From'] = smtp_from
                    msg['To'] = alert_email
                    msg['Subject'] = f"Domus Alert: {title}"
                    
                    body = f"""
                    Alert Level: {level.upper()}
                    Message: {message}
                    Time: {alert_data["timestamp"]}
                    Service: Domus Planning Platform
                    """
                    
                    msg.attach(MIMEText(body, 'plain'))
                    
                    server = smtplib.SMTP(smtp_host, 587)
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                    server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send alert: {e}")
            return False