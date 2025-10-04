"""
Comprehensive Alert System with Slack and Email Notifications
Handles system alerts, job failures, and monitoring notifications
"""

import os
import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import redis
from jinja2 import Template

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"  # Future implementation
    WEBHOOK = "webhook"  # Future implementation

@dataclass
class Alert:
    id: str
    title: str
    message: str
    level: AlertLevel
    channels: List[AlertChannel]
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivery_status: Dict[str, str] = None
    metadata: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    
    def __post_init__(self):
        if self.delivery_status is None:
            self.delivery_status = {}

class AlertThrottle:
    """Prevents alert spam by throttling similar alerts"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.throttle_window = 3600  # 1 hour in seconds
        
    def should_send_alert(self, alert_key: str, max_per_window: int = 5) -> bool:
        """Check if alert should be sent based on throttling rules"""
        try:
            count_key = f"alert_throttle:{alert_key}"
            current_count = self.redis.get(count_key)
            
            if current_count is None:
                # First alert in window
                self.redis.setex(count_key, self.throttle_window, 1)
                return True
            
            count = int(current_count)
            if count < max_per_window:
                self.redis.incr(count_key)
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking alert throttle: {e}")
            return True  # Allow alert if throttle check fails

class SlackNotifier:
    """Slack notification handler"""
    
    def __init__(self):
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.token = os.getenv('SLACK_BOT_TOKEN')
        self.channel = os.getenv('SLACK_ALERT_CHANNEL', '#alerts')
        self.enabled = bool(self.webhook_url or self.token)
        
        if not self.enabled:
            logging.warning("Slack notifications disabled - no webhook URL or token configured")
    
    def send_notification(self, alert: Alert) -> Dict[str, Any]:
        """Send Slack notification"""
        if not self.enabled:
            return {'status': 'disabled', 'message': 'Slack not configured'}
        
        try:
            payload = self._build_slack_payload(alert)
            
            if self.webhook_url:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
            else:
                # Use Slack API with bot token
                headers = {
                    'Authorization': f'Bearer {self.token}',
                    'Content-Type': 'application/json'
                }
                response = requests.post(
                    'https://slack.com/api/chat.postMessage',
                    json=payload,
                    headers=headers,
                    timeout=10
                )
            
            if response.status_code == 200:
                return {'status': 'success', 'response': response.json()}
            else:
                return {
                    'status': 'error',
                    'message': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _build_slack_payload(self, alert: Alert) -> Dict[str, Any]:
        """Build Slack message payload"""
        # Color coding for alert levels
        colors = {
            AlertLevel.INFO: "#36a64f",      # Green
            AlertLevel.WARNING: "#ff9500",   # Orange
            AlertLevel.ERROR: "#ff0000",     # Red
            AlertLevel.CRITICAL: "#8b0000"   # Dark Red
        }
        
        # Emoji for alert levels
        emojis = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        fields = [
            {
                "title": "Level",
                "value": alert.level.value.upper(),
                "short": True
            },
            {
                "title": "Time",
                "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": True
            }
        ]
        
        # Add metadata fields if present
        if alert.metadata:
            for key, value in alert.metadata.items():
                if len(fields) < 8:  # Slack limit
                    fields.append({
                        "title": key.replace('_', ' ').title(),
                        "value": str(value)[:100],  # Truncate long values
                        "short": True
                    })
        
        attachment = {
            "color": colors.get(alert.level, "#cccccc"),
            "title": f"{emojis.get(alert.level, '')} {alert.title}",
            "text": alert.message,
            "fields": fields,
            "footer": "Domus Platform Monitoring",
            "ts": int(alert.created_at.timestamp())
        }
        
        payload = {
            "channel": self.channel,
            "username": "Domus Monitor",
            "icon_emoji": ":warning:",
            "attachments": [attachment]
        }
        
        return payload

class EmailNotifier:
    """Email notification handler"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.to_emails = os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
        self.enabled = bool(self.smtp_username and self.smtp_password and self.to_emails)
        
        if not self.enabled:
            logging.warning("Email notifications disabled - SMTP not configured")
    
    def send_notification(self, alert: Alert) -> Dict[str, Any]:
        """Send email notification"""
        if not self.enabled:
            return {'status': 'disabled', 'message': 'Email not configured'}
        
        try:
            msg = self._build_email_message(alert)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                for to_email in self.to_emails:
                    if to_email.strip():
                        server.send_message(msg, to_addrs=[to_email.strip()])
            
            return {'status': 'success', 'recipients': len(self.to_emails)}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _build_email_message(self, alert: Alert) -> MIMEMultipart:
        """Build email message"""
        msg = MIMEMultipart('alternative')
        
        # Subject with alert level
        subject_prefix = {
            AlertLevel.INFO: "[INFO]",
            AlertLevel.WARNING: "[WARNING]",
            AlertLevel.ERROR: "[ERROR]",
            AlertLevel.CRITICAL: "[CRITICAL]"
        }
        
        msg['Subject'] = f"{subject_prefix.get(alert.level, '[ALERT]')} {alert.title}"
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        
        # Plain text version
        text_content = self._build_text_email(alert)
        text_part = MIMEText(text_content, 'plain')
        msg.attach(text_part)
        
        # HTML version
        html_content = self._build_html_email(alert)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        return msg
    
    def _build_text_email(self, alert: Alert) -> str:
        """Build plain text email content"""
        content = f"""
DOMUS PLATFORM ALERT

Title: {alert.title}
Level: {alert.level.value.upper()}
Time: {alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}

Message:
{alert.message}

"""
        
        if alert.metadata:
            content += "Additional Information:\n"
            for key, value in alert.metadata.items():
                content += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        content += f"""
Alert ID: {alert.id}

--
Domus Platform Monitoring System
"""
        
        return content
    
    def _build_html_email(self, alert: Alert) -> str:
        """Build HTML email content"""
        # Color coding for alert levels
        level_colors = {
            AlertLevel.INFO: "#d4edda",
            AlertLevel.WARNING: "#fff3cd",
            AlertLevel.ERROR: "#f8d7da",
            AlertLevel.CRITICAL: "#f5c6cb"
        }
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ alert.title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .alert-level { padding: 10px 20px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 20px; background-color: {{ level_color }}; }
        .message { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .metadata { margin-top: 20px; }
        .metadata table { width: 100%; border-collapse: collapse; }
        .metadata th, .metadata td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .metadata th { background-color: #f8f9fa; }
        .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Domus Platform Alert</h1>
            <h2>{{ alert.title }}</h2>
        </div>
        
        <div class="alert-level">
            Alert Level: {{ alert.level.value.upper() }}
        </div>
        
        <div class="message">
            <h3>Message:</h3>
            <p>{{ alert.message }}</p>
        </div>
        
        <p><strong>Time:</strong> {{ alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") }}</p>
        
        {% if alert.metadata %}
        <div class="metadata">
            <h3>Additional Information:</h3>
            <table>
                {% for key, value in alert.metadata.items() %}
                <tr>
                    <th>{{ key.replace('_', ' ').title() }}</th>
                    <td>{{ value }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>Alert ID: {{ alert.id }}</p>
            <p>Domus Platform Monitoring System</p>
        </div>
    </div>
</body>
</html>
        """)
        
        return template.render(
            alert=alert,
            level_color=level_colors.get(alert.level, "#f8f9fa")
        )

class AlertSystem:
    """Central alert management system"""
    
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        self.slack_notifier = SlackNotifier()
        self.email_notifier = EmailNotifier()
        self.throttle = AlertThrottle(self.redis_client)
        self.logger = logging.getLogger(__name__)
        
        # Alert configuration
        self.retry_attempts = 3
        self.retry_delay = 300  # 5 minutes
        
    def send_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        channels: List[AlertChannel] = None,
        metadata: Optional[Dict[str, Any]] = None,
        throttle_key: Optional[str] = None,
        max_per_window: int = 5
    ) -> str:
        """Send an alert through specified channels"""
        
        if channels is None:
            channels = [AlertChannel.SLACK, AlertChannel.EMAIL]
        
        # Generate alert ID
        alert_id = f"alert_{int(datetime.utcnow().timestamp())}_{hash(title + message) % 10000}"
        
        # Check throttling
        if throttle_key and not self.throttle.should_send_alert(throttle_key, max_per_window):
            self.logger.info(f"Alert throttled: {throttle_key}")
            return alert_id
        
        # Create alert object
        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            level=level,
            channels=channels,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store alert
        self._store_alert(alert)
        
        # Send notifications
        self._send_notifications(alert)
        
        self.logger.info(f"Alert sent: {alert_id} - {title}")
        
        return alert_id
    
    def _send_notifications(self, alert: Alert):
        """Send notifications through all specified channels"""
        for channel in alert.channels:
            try:
                if channel == AlertChannel.SLACK:
                    result = self.slack_notifier.send_notification(alert)
                elif channel == AlertChannel.EMAIL:
                    result = self.email_notifier.send_notification(alert)
                else:
                    result = {'status': 'unsupported', 'message': f'Channel {channel} not implemented'}
                
                # Update delivery status
                alert.delivery_status[channel.value] = result['status']
                
                if result['status'] != 'success':
                    self.logger.error(f"Failed to send alert via {channel.value}: {result.get('message')}")
                    
                    # Schedule retry for failed notifications
                    if result['status'] == 'error' and alert.retry_count < self.retry_attempts:
                        self._schedule_retry(alert, channel)
                
            except Exception as e:
                self.logger.error(f"Error sending alert via {channel.value}: {e}")
                alert.delivery_status[channel.value] = 'error'
        
        # Update alert with delivery status
        alert.sent_at = datetime.utcnow()
        self._store_alert(alert)
    
    def _schedule_retry(self, alert: Alert, channel: AlertChannel):
        """Schedule alert retry for failed delivery"""
        # This would integrate with the job scheduler for retries
        # For now, just log the retry intention
        self.logger.info(f"Scheduling retry for alert {alert.id} on channel {channel.value}")
    
    def _store_alert(self, alert: Alert):
        """Store alert in Redis for history tracking"""
        try:
            alert_data = asdict(alert)
            
            # Convert datetime objects to ISO format
            alert_data['created_at'] = alert.created_at.isoformat()
            if alert.sent_at:
                alert_data['sent_at'] = alert.sent_at.isoformat()
            
            # Convert enums to strings
            alert_data['level'] = alert.level.value
            alert_data['channels'] = [ch.value for ch in alert.channels]
            
            self.redis_client.setex(
                f"alert:{alert.id}",
                timedelta(days=30),  # Keep alerts for 30 days
                json.dumps(alert_data)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store alert {alert.id}: {e}")
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Retrieve a specific alert"""
        try:
            data = self.redis_client.get(f"alert:{alert_id}")
            if not data:
                return None
            
            alert_data = json.loads(data)
            
            # Convert back to objects
            alert_data['level'] = AlertLevel(alert_data['level'])
            alert_data['channels'] = [AlertChannel(ch) for ch in alert_data['channels']]
            alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
            if alert_data.get('sent_at'):
                alert_data['sent_at'] = datetime.fromisoformat(alert_data['sent_at'])
            
            return Alert(**alert_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get alert {alert_id}: {e}")
            return None
    
    def get_recent_alerts(self, limit: int = 50) -> List[Alert]:
        """Get recent alerts"""
        try:
            alert_keys = self.redis_client.keys("alert:*")
            alerts = []
            
            for key in alert_keys[-limit:]:
                alert_id = key.decode().split(':')[1]
                alert = self.get_alert(alert_id)
                if alert:
                    alerts.append(alert)
            
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            alerts = self.get_recent_alerts(1000)  # Get more for statistics
            
            if not alerts:
                return {}
            
            # Calculate statistics
            total_alerts = len(alerts)
            alerts_by_level = {}
            alerts_by_channel = {}
            successful_deliveries = 0
            failed_deliveries = 0
            
            for alert in alerts:
                # Count by level
                level = alert.level.value
                alerts_by_level[level] = alerts_by_level.get(level, 0) + 1
                
                # Count by channel
                for channel in alert.channels:
                    channel_name = channel.value
                    alerts_by_channel[channel_name] = alerts_by_channel.get(channel_name, 0) + 1
                
                # Count delivery success/failure
                if alert.delivery_status:
                    for status in alert.delivery_status.values():
                        if status == 'success':
                            successful_deliveries += 1
                        elif status in ['error', 'failed']:
                            failed_deliveries += 1
            
            # Recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_alerts = [a for a in alerts if a.created_at > recent_cutoff]
            
            return {
                'total_alerts': total_alerts,
                'alerts_by_level': alerts_by_level,
                'alerts_by_channel': alerts_by_channel,
                'successful_deliveries': successful_deliveries,
                'failed_deliveries': failed_deliveries,
                'delivery_success_rate': (successful_deliveries / (successful_deliveries + failed_deliveries)) * 100 if (successful_deliveries + failed_deliveries) > 0 else 0,
                'recent_alerts_24h': len(recent_alerts),
                'most_recent_alert': alerts[0].created_at.isoformat() if alerts else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get alert statistics: {e}")
            return {}

# Health check for alert system
def check_alert_system_health() -> Dict[str, Any]:
    """Check if alert system is functioning properly"""
    try:
        alert_system = AlertSystem()
        
        # Test Redis connection
        alert_system.redis_client.ping()
        
        # Check notifier configurations
        slack_enabled = alert_system.slack_notifier.enabled
        email_enabled = alert_system.email_notifier.enabled
        
        if not slack_enabled and not email_enabled:
            return {
                'status': 'unhealthy',
                'message': 'No notification channels configured'
            }
        
        return {
            'status': 'healthy',
            'slack_enabled': slack_enabled,
            'email_enabled': email_enabled,
            'message': 'Alert system operational'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': f'Alert system check failed: {e}'
        }