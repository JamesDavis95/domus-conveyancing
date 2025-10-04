"""
Security Hardening Module
Implements comprehensive security measures for production deployment
"""

import secrets
import hashlib
import time
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from collections import defaultdict, deque
import pyotp
import qrcode
from io import BytesIO
import base64
from flask import request, session, jsonify, abort, g
from werkzeug.security import generate_password_hash
import bcrypt

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(lambda: {'count': 0, 'window_start': time.time()})
failed_attempts = defaultdict(list)

class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self):
        self.max_login_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.session_timeout = 3600  # 1 hour
        self.password_min_length = 12
        self.rate_limits = {
            'api': {'requests': 100, 'window': 60},
            'auth': {'requests': 5, 'window': 300},
            'upload': {'requests': 10, 'window': 60}
        }
        
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with random salt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        issues = []
        score = 0
        
        if len(password) < self.password_min_length:
            issues.append(f"Password must be at least {self.password_min_length} characters long")
        else:
            score += 20
            
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain lowercase letters")
        else:
            score += 20
            
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain uppercase letters")
        else:
            score += 20
            
        if not re.search(r'\d', password):
            issues.append("Password must contain numbers")
        else:
            score += 20
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain special characters")
        else:
            score += 20
            
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            issues.append("Password should not contain repeated characters")
            score -= 10
            
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            issues.append("Password should not contain sequential characters")
            score -= 10
        
        return {
            'valid': len(issues) == 0,
            'score': max(0, score),
            'issues': issues,
            'strength': 'Weak' if score < 60 else 'Medium' if score < 80 else 'Strong'
        }


class TwoFactorAuth:
    """Two-Factor Authentication implementation"""
    
    def __init__(self):
        self.issuer_name = "Domus Planning"
        
    def generate_secret(self) -> str:
        """Generate new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, email: str, secret: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            email,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        if not token or len(token) != 6:
            return False
            
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        
    def is_allowed(self, identifier: str, limit_type: str = 'api') -> Dict[str, Any]:
        """Check if request is within rate limit"""
        limits = SecurityManager().rate_limits.get(limit_type, {'requests': 100, 'window': 60})
        max_requests = limits['requests']
        window_seconds = limits['window']
        
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        requests = self.requests[identifier]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= max_requests:
            return {
                'allowed': False,
                'retry_after': int(requests[0] + window_seconds - now),
                'remaining': 0
            }
        
        # Add current request
        requests.append(now)
        
        return {
            'allowed': True,
            'remaining': max_requests - len(requests),
            'reset_time': int(now + window_seconds)
        }


class CaptchaService:
    """CAPTCHA implementation for bot protection"""
    
    def __init__(self):
        self.captcha_storage = {}
        self.captcha_timeout = 300  # 5 minutes
    
    def generate_captcha(self) -> Dict[str, str]:
        """Generate simple math CAPTCHA"""
        import random
        
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"{num1} + {num2}"
        elif operation == '-':
            answer = max(num1, num2) - min(num1, num2)
            question = f"{max(num1, num2)} - {min(num1, num2)}"
        else:  # multiplication
            num1 = random.randint(1, 10)
            num2 = random.randint(1, 10)
            answer = num1 * num2
            question = f"{num1} × {num2}"
        
        captcha_id = secrets.token_urlsafe(16)
        self.captcha_storage[captcha_id] = {
            'answer': str(answer),
            'expires': time.time() + self.captcha_timeout
        }
        
        return {
            'captcha_id': captcha_id,
            'question': f"What is {question}?",
            'expires_in': self.captcha_timeout
        }
    
    def verify_captcha(self, captcha_id: str, answer: str) -> bool:
        """Verify CAPTCHA answer"""
        if captcha_id not in self.captcha_storage:
            return False
        
        captcha_data = self.captcha_storage[captcha_id]
        
        # Check expiration
        if time.time() > captcha_data['expires']:
            del self.captcha_storage[captcha_id]
            return False
        
        # Verify answer
        is_correct = str(answer).strip() == captcha_data['answer']
        
        # Remove used captcha
        del self.captcha_storage[captcha_id]
        
        return is_correct


class CSPManager:
    """Content Security Policy management"""
    
    def __init__(self):
        self.csp_policies = {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Needed for inline scripts
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://js.stripe.com"
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "blob:"
            ],
            'font-src': [
                "'self'",
                "https://cdnjs.cloudflare.com"
            ],
            'connect-src': [
                "'self'",
                "https://api.stripe.com"
            ],
            'frame-src': [
                "https://js.stripe.com"
            ],
            'worker-src': ["'self'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'none'"]
        }
    
    def generate_csp_header(self) -> str:
        """Generate CSP header string"""
        directives = []
        for directive, sources in self.csp_policies.items():
            directives.append(f"{directive} {' '.join(sources)}")
        return '; '.join(directives)


class LogRedactor:
    """Log redaction for sensitive data"""
    
    def __init__(self):
        self.sensitive_patterns = [
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
            (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), '[CARD]'),
            (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
            (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', re.IGNORECASE), 'password=[REDACTED]'),
            (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', re.IGNORECASE), 'token=[REDACTED]'),
            (re.compile(r'key["\']?\s*[:=]\s*["\']?([^"\'\\s]+)', re.IGNORECASE), 'key=[REDACTED]'),
        ]
    
    def redact_log_message(self, message: str) -> str:
        """Redact sensitive information from log message"""
        for pattern, replacement in self.sensitive_patterns:
            message = pattern.sub(replacement, message)
        return message


# Global instances
security_manager = SecurityManager()
two_factor_auth = TwoFactorAuth()
rate_limiter = RateLimiter()
captcha_service = CaptchaService()
csp_manager = CSPManager()
log_redactor = LogRedactor()


# Decorators for security enforcement
def require_2fa(f):
    """Decorator to require 2FA for sensitive operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('2fa_verified'):
            return jsonify({'error': 'Two-factor authentication required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(limit_type: str = 'api'):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.remote_addr
            if 'user_id' in session:
                identifier = f"user_{session['user_id']}"
            
            result = rate_limiter.is_allowed(identifier, limit_type)
            
            if not result['allowed']:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': result['retry_after']
                }), 429
            
            # Add rate limit headers
            g.rate_limit_remaining = result['remaining']
            g.rate_limit_reset = result.get('reset_time')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_captcha(f):
    """Decorator to require CAPTCHA verification"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if CAPTCHA verification is needed
        identifier = request.remote_addr
        recent_failures = [
            attempt for attempt in failed_attempts[identifier]
            if time.time() - attempt < 300  # 5 minutes
        ]
        
        if len(recent_failures) >= 3:
            # Require CAPTCHA after 3 failed attempts
            captcha_id = request.json.get('captcha_id') if request.is_json else request.form.get('captcha_id')
            captcha_answer = request.json.get('captcha_answer') if request.is_json else request.form.get('captcha_answer')
            
            if not captcha_id or not captcha_answer:
                captcha_data = captcha_service.generate_captcha()
                return jsonify({
                    'error': 'CAPTCHA verification required',
                    'captcha': captcha_data
                }), 428  # Precondition Required
            
            if not captcha_service.verify_captcha(captcha_id, captcha_answer):
                return jsonify({'error': 'Invalid CAPTCHA'}), 400
        
        return f(*args, **kwargs)
    return decorated_function


def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security events with redaction"""
    event_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': request.remote_addr if request else 'unknown',
        'user_agent': request.headers.get('User-Agent') if request else 'unknown',
        'user_id': session.get('user_id') if 'session' in globals() and session else None,
        'details': details
    }
    
    # Redact sensitive information
    log_message = json.dumps(event_data)
    redacted_message = log_redactor.redact_log_message(log_message)
    
    security_logger.info(f"SECURITY_EVENT: {redacted_message}")


# Security middleware
class SecurityMiddleware:
    """Flask middleware for security headers and checks"""
    
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        def new_start_response(status, response_headers):
            # Add security headers
            security_headers = [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Content-Security-Policy', csp_manager.generate_csp_header()),
                ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                ('Permissions-Policy', 'geolocation=(), microphone=(), camera=()'),
            ]
            
            # Add rate limit headers if present
            if hasattr(g, 'rate_limit_remaining'):
                security_headers.append(('X-RateLimit-Remaining', str(g.rate_limit_remaining)))
            if hasattr(g, 'rate_limit_reset'):
                security_headers.append(('X-RateLimit-Reset', str(g.rate_limit_reset)))
            
            response_headers.extend(security_headers)
            return start_response(status, response_headers)
        
        return self.app(environ, new_start_response)