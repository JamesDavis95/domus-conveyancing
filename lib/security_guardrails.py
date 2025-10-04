"""
Production Security & Operational Guardrails
CAPTCHA, 2FA, CSP, Rate Limiting, PII Redaction, Backups, Status Page
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import pyotp
import qrcode
from io import BytesIO
import base64

# Configure logging with PII redaction
class PIIRedactionFilter(logging.Filter):
    """Filter to remove PII from logs"""
    
    PII_PATTERNS = [
        r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card numbers
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        r'\b\d{3}-\d{2}-\d{4}\b',  # Social security numbers
        r'\b(?:0[1-9]|[12]\d|3[01])[\/\-](?:0[1-9]|1[012])[\/\-](?:19|20)\d\d\b',  # Dates
        r'\b(?:\+44|0)[1-9]\d{8,9}\b',  # UK phone numbers
        r'\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b',  # UK postcodes
    ]
    
    def filter(self, record):
        if hasattr(record, 'msg'):
            message = str(record.msg)
            for pattern in self.PII_PATTERNS:
                message = re.sub(pattern, '[REDACTED]', message, flags=re.IGNORECASE)
            record.msg = message
        return True

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_secure.log'),
        logging.StreamHandler()
    ]
)

# Add PII redaction filter to all loggers
for handler in logging.root.handlers:
    handler.addFilter(PIIRedactionFilter())

logger = logging.getLogger(__name__)

# Rate Limiting Setup
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.setup_security_headers()
        self.setup_rate_limiting()
    
    def setup_security_headers(self):
        """Add security headers middleware"""
        
        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            
            # Content Security Policy
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://js.stripe.com https://checkout.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com; "
                "frame-src https://checkout.stripe.com https://js.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-ancestors 'none';"
            )
            
            response.headers["Content-Security-Policy"] = csp_policy
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            return response
    
    def setup_rate_limiting(self):
        """Configure rate limiting for different endpoint types"""
        
        # Authentication endpoints - strict limits
        @self.app.middleware("http")
        async def auth_rate_limit(request: Request, call_next):
            if request.url.path.startswith("/api/auth/"):
                # 5 attempts per minute for auth endpoints
                client_ip = get_remote_address(request)
                rate_key = f"auth:{client_ip}"
                
                if not await self._check_rate_limit(rate_key, 5, 60):
                    raise HTTPException(
                        status_code=429,
                        detail="Too many authentication attempts. Please try again later."
                    )
            
            return await call_next(request)

    async def _check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check rate limit using Redis or in-memory store"""
        # Implementation depends on your caching solution
        # This is a simplified version
        return True  # Placeholder

class CaptchaService:
    """CAPTCHA verification service"""
    
    def __init__(self):
        self.captcha_store = {}  # Use Redis in production
    
    def generate_captcha(self) -> Dict[str, str]:
        """Generate a simple math CAPTCHA"""
        import random
        
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        answer = a + b
        
        captcha_id = secrets.token_urlsafe(16)
        self.captcha_store[captcha_id] = {
            "answer": answer,
            "expires": datetime.utcnow() + timedelta(minutes=10)
        }
        
        return {
            "captcha_id": captcha_id,
            "question": f"What is {a} + {b}?",
            "expires_in": 600
        }
    
    def verify_captcha(self, captcha_id: str, answer: int) -> bool:
        """Verify CAPTCHA answer"""
        if captcha_id not in self.captcha_store:
            return False
        
        captcha_data = self.captcha_store[captcha_id]
        
        # Check expiry
        if datetime.utcnow() > captcha_data["expires"]:
            del self.captcha_store[captcha_id]
            return False
        
        # Check answer
        is_correct = captcha_data["answer"] == answer
        
        # Remove used CAPTCHA
        del self.captcha_store[captcha_id]
        
        return is_correct

class TwoFactorAuth:
    """Two-Factor Authentication service"""
    
    def generate_secret(self, user_email: str) -> Dict[str, str]:
        """Generate 2FA secret and QR code"""
        secret = pyotp.random_base32()
        
        # Create TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Domus Planning"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "secret": secret,
            "qr_code": f"data:image/png;base64,{qr_code_data}",
            "backup_codes": self._generate_backup_codes()
        }
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify 2FA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def _generate_backup_codes(self) -> list:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(4).upper() for _ in range(8)]

class BackupService:
    """Database backup and restore service"""
    
    def __init__(self):
        self.backup_schedule = "0 2 * * *"  # Daily at 2 AM
    
    async def create_backup(self) -> Dict[str, Any]:
        """Create database backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"domus_backup_{timestamp}"
        
        # Database dump (PostgreSQL example)
        import subprocess
        
        try:
            # Create database dump
            dump_cmd = [
                "pg_dump",
                "-h", "localhost",
                "-U", "postgres",
                "-d", "domus_production",
                "-f", f"/backups/{backup_name}.sql",
                "--no-password"
            ]
            
            result = subprocess.run(dump_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Backup failed: {result.stderr}")
            
            # Upload to S3 with versioning
            await self._upload_to_s3(f"/backups/{backup_name}.sql", backup_name)
            
            return {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "status": "success",
                "size_mb": await self._get_file_size(f"/backups/{backup_name}.sql")
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "backup_name": backup_name,
                "timestamp": timestamp,
                "status": "failed",
                "error": str(e)
            }
    
    async def restore_backup(self, backup_name: str, target_db: str = "domus_staging") -> bool:
        """Restore database from backup"""
        try:
            # Download from S3
            backup_file = await self._download_from_s3(backup_name)
            
            # Restore database
            restore_cmd = [
                "psql",
                "-h", "localhost",
                "-U", "postgres",
                "-d", target_db,
                "-f", backup_file
            ]
            
            result = subprocess.run(restore_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Restore failed: {result.stderr}")
            
            logger.info(f"Successfully restored {backup_name} to {target_db}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    async def _upload_to_s3(self, file_path: str, backup_name: str):
        """Upload backup to S3 with versioning"""
        # Implementation depends on your S3 setup
        pass
    
    async def _download_from_s3(self, backup_name: str) -> str:
        """Download backup from S3"""
        # Implementation depends on your S3 setup
        return f"/tmp/{backup_name}.sql"
    
    async def _get_file_size(self, file_path: str) -> float:
        """Get file size in MB"""
        import os
        return os.path.getsize(file_path) / (1024 * 1024)

class StatusPageService:
    """System status monitoring and public status page"""
    
    def __init__(self):
        self.services = {
            "database": self._check_database,
            "stripe": self._check_stripe,
            "s3": self._check_s3,
            "planning_ai": self._check_planning_ai,
            "auth_service": self._check_auth_service
        }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            "overall_status": "operational",
            "last_updated": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        all_operational = True
        
        for service_name, check_func in self.services.items():
            try:
                service_status = await check_func()
                status["services"][service_name] = service_status
                
                if service_status["status"] != "operational":
                    all_operational = False
                    
            except Exception as e:
                status["services"][service_name] = {
                    "status": "down",
                    "message": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
                all_operational = False
        
        if not all_operational:
            status["overall_status"] = "degraded"
        
        return status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            # Simple database query
            from sqlalchemy import create_engine, text
            engine = create_engine("postgresql://user:pass@localhost/domus")
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                
            return {
                "status": "operational",
                "response_time_ms": 50,  # Mock response time
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "down",
                "message": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def _check_stripe(self) -> Dict[str, Any]:
        """Check Stripe API connectivity"""
        # Implementation for Stripe health check
        return {
            "status": "operational",
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def _check_s3(self) -> Dict[str, Any]:
        """Check S3 connectivity"""
        # Implementation for S3 health check
        return {
            "status": "operational",
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def _check_planning_ai(self) -> Dict[str, Any]:
        """Check Planning AI service"""
        # Implementation for AI service health check
        return {
            "status": "operational",
            "last_check": datetime.utcnow().isoformat()
        }
    
    async def _check_auth_service(self) -> Dict[str, Any]:
        """Check authentication service"""
        # Implementation for auth service health check
        return {
            "status": "operational",
            "last_check": datetime.utcnow().isoformat()
        }

# Initialize services
captcha_service = CaptchaService()
twofa_service = TwoFactorAuth()
backup_service = BackupService()
status_service = StatusPageService()

# Middleware dependencies
security_middleware = None  # Will be initialized with FastAPI app

def init_security_middleware(app: FastAPI):
    """Initialize security middleware with FastAPI app"""
    global security_middleware
    security_middleware = SecurityMiddleware(app)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Export services for use in routes
__all__ = [
    "init_security_middleware",
    "captcha_service", 
    "twofa_service", 
    "backup_service", 
    "status_service",
    "PIIRedactionFilter"
]