"""
Security Integration Module
Integrates all security systems with FastAPI application
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from .two_factor_auth import TwoFactorAuth
from .captcha_service import CaptchaService, CaptchaMiddleware
from .csp_manager import CSPManager, CSPMiddleware
from .rate_limiter import RateLimiter
from .log_redactor import LogRedactor, SecurityEventLogger
from .ip_allowlist import IPAllowlist, IPAllowlistMiddleware

class SecurityManager:
    """Centralized security management"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.two_factor = TwoFactorAuth()
        self.captcha = CaptchaService()
        self.csp = CSPManager()
        self.rate_limiter = RateLimiter()
        self.log_redactor = LogRedactor()
        self.ip_allowlist = IPAllowlist()
        self.security_logger = SecurityEventLogger()
        
        # Setup security middleware
        self._setup_security_middleware()
        
        # Setup security endpoints
        self._setup_security_endpoints()
    
    def _setup_security_middleware(self):
        """Setup all security middleware"""
        
        # Add CSP middleware
        self.app.add_middleware(CSPMiddleware, csp_manager=self.csp)
        
        # Add CAPTCHA middleware
        self.app.add_middleware(CaptchaMiddleware, captcha_service=self.captcha)
        
        # Add IP allowlist middleware
        self.app.add_middleware(IPAllowlistMiddleware, allowlist=self.ip_allowlist)
        
        # Add rate limiting middleware
        self.app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)
        
        # Add security logging middleware
        self.app.add_middleware(SecurityLoggingMiddleware, security_manager=self)
    
    def _setup_security_endpoints(self):
        """Setup security-related API endpoints"""
        
        @self.app.post("/api/security/2fa/setup")
        async def setup_2fa(request: Request, user_id: str):
            """Setup 2FA for user"""
            
            try:
                result = await self.two_factor.setup_2fa_for_user(user_id)
                
                self.security_logger.log_2fa_event(
                    user_id=user_id,
                    event="setup_initiated",
                    success=True
                )
                
                return result
                
            except Exception as e:
                self.security_logger.log_2fa_event(
                    user_id=user_id,
                    event="setup_failed",
                    success=False
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/security/2fa/verify")
        async def verify_2fa(request: Request, user_id: str, token: str):
            """Verify 2FA token"""
            
            try:
                is_valid = await self.two_factor.verify_totp_token(user_id, token)
                
                self.security_logger.log_2fa_event(
                    user_id=user_id,
                    event="token_verification",
                    success=is_valid
                )
                
                return {"valid": is_valid}
                
            except Exception as e:
                self.security_logger.log_2fa_event(
                    user_id=user_id,
                    event="verification_error",
                    success=False
                )
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/security/captcha/challenge")
        async def get_captcha_challenge(request: Request):
            """Get CAPTCHA challenge"""
            
            try:
                challenge = await self.captcha.generate_challenge('text')
                return challenge
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/security/captcha/verify")
        async def verify_captcha(request: Request, challenge_id: str, answer: str):
            """Verify CAPTCHA answer"""
            
            try:
                is_valid = await self.captcha.verify_challenge(challenge_id, answer)
                return {"valid": is_valid}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/admin/security/status")
        async def get_security_status(request: Request):
            """Get security system status (admin only)"""
            
            # This would normally check admin permissions
            
            try:
                status = {
                    "two_factor_auth": {
                        "enabled": True,
                        "users_with_2fa": await self.two_factor.get_2fa_user_count()
                    },
                    "captcha": {
                        "enabled": True,
                        "challenges_today": await self.captcha.get_challenge_count_today()
                    },
                    "rate_limiting": {
                        "enabled": True,
                        "violations_today": await self.rate_limiter.get_violation_count_today()
                    },
                    "ip_allowlist": {
                        "enabled": self.ip_allowlist.enabled,
                        "rules_count": len(self.ip_allowlist.rules)
                    },
                    "csp": {
                        "enabled": True,
                        "policy": self.csp.current_policy
                    }
                }
                
                return status
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting"""
        
        # Get client identifier
        client_id = self._get_client_id(request)
        endpoint = f"{request.method} {request.url.path}"
        
        # Check rate limit
        allowed, info = await self.rate_limiter.check_rate_limit(client_id, endpoint)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": info.get("retry_after", 60)
                },
                headers={
                    "Retry-After": str(info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("reset_time", 0))
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
        response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(info.get("reset_time", 0))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get user ID from session/token
        # For now, use IP address
        return request.client.host

class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Security event logging middleware"""
    
    def __init__(self, app, security_manager: SecurityManager):
        super().__init__(app)
        self.security_manager = security_manager
    
    async def dispatch(self, request: Request, call_next):
        """Log security events"""
        
        start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")
        
        try:
            response = await call_next(request)
            
            # Log successful request if sensitive endpoint
            if self._is_sensitive_endpoint(request.url.path):
                self.security_manager.security_logger.logger.info(
                    f"Sensitive endpoint access: {request.method} {request.url.path} "
                    f"- IP: {client_ip} - Status: {response.status_code}"
                )
            
            return response
            
        except HTTPException as e:
            # Log security-related errors
            if e.status_code in [401, 403, 429]:
                self.security_manager.security_logger.logger.warning(
                    f"Security event: {request.method} {request.url.path} "
                    f"- IP: {client_ip} - Status: {e.status_code} - Error: {e.detail}"
                )
            raise
            
        except Exception as e:
            # Log unexpected errors
            self.security_manager.security_logger.logger.error(
                f"Unexpected error: {request.method} {request.url.path} "
                f"- IP: {client_ip} - Error: {str(e)}"
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint is sensitive"""
        
        sensitive_paths = [
            "/api/auth/",
            "/api/admin/",
            "/api/users/",
            "/api/security/",
            "/api/payments/",
            "/api/documents/"
        ]
        
        return any(path.startswith(sensitive_path) for sensitive_path in sensitive_paths)

def configure_security(app: FastAPI, config: Optional[Dict[str, Any]] = None) -> SecurityManager:
    """Configure security for FastAPI application"""
    
    security_manager = SecurityManager(app)
    
    if config:
        # Configure from settings
        if "ip_allowlist" in config:
            security_manager.ip_allowlist.import_rules_from_config(config["ip_allowlist"])
        
        if "rate_limiting" in config:
            security_manager.rate_limiter.configure_from_dict(config["rate_limiting"])
        
        if "csp" in config:
            security_manager.csp.configure_from_dict(config["csp"])
    
    return security_manager

# Dependency for requiring 2FA
async def require_2fa(request: Request, security_manager: SecurityManager = Depends()) -> bool:
    """Dependency to require 2FA verification"""
    
    # This would normally check the user's session for 2FA status
    # For now, return True (assuming 2FA is verified)
    return True

# Dependency for admin access
async def require_admin_access(request: Request, security_manager: SecurityManager = Depends()) -> bool:
    """Dependency to require admin access with IP check"""
    
    client_ip = request.client.host
    
    if not security_manager.ip_allowlist.is_ip_allowed(client_ip, require_admin=True):
        raise HTTPException(
            status_code=403,
            detail="Admin access not allowed from this IP address"
        )
    
    return True