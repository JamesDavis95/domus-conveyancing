"""
reCAPTCHA v3 Integration for Form Protection

Provides server-side reCAPTCHA v3 verification with proper secret key protection.
Includes score-based analysis and adaptive security policies.
"""

import aiohttp
import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse
import os
import logging

# Import your caching system
try:
    from cache_system import cache_manager
except ImportError:
    # Fallback in-memory cache
    cache_manager = None

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ReCAPTCHAResponse:
    """reCAPTCHA verification response"""
    success: bool
    score: float
    action: str
    challenge_ts: Optional[str] = None
    hostname: Optional[str] = None
    error_codes: Optional[List[str]] = None
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> 'ReCAPTCHAResponse':
        """Create response from Google reCAPTCHA API response"""
        return cls(
            success=response_data.get('success', False),
            score=response_data.get('score', 0.0),
            action=response_data.get('action', ''),
            challenge_ts=response_data.get('challenge_ts'),
            hostname=response_data.get('hostname'),
            error_codes=response_data.get('error-codes', [])
        )

@dataclass
class SecurityPolicy:
    """Security policy for different actions"""
    action: str
    min_score: float
    description: str
    block_threshold: float = 0.3
    suspicious_threshold: float = 0.5
    
    def evaluate(self, score: float) -> Dict[str, Any]:
        """Evaluate score against policy"""
        if score < self.block_threshold:
            return {
                'action': 'block',
                'level': 'high_risk',
                'message': 'Request blocked due to high bot probability'
            }
        elif score < self.suspicious_threshold:
            return {
                'action': 'challenge',
                'level': 'medium_risk', 
                'message': 'Additional verification required'
            }
        elif score < self.min_score:
            return {
                'action': 'monitor',
                'level': 'low_risk',
                'message': 'Request flagged for monitoring'
            }
        else:
            return {
                'action': 'allow',
                'level': 'trusted',
                'message': 'Request approved'
            }

class ReCAPTCHAService:
    """Service for reCAPTCHA v3 integration"""
    
    def __init__(self):
        self.secret_key = os.getenv('RECAPTCHA_SECRET_KEY')
        self.site_key = os.getenv('RECAPTCHA_SITE_KEY')
        
        if not self.secret_key:
            logger.warning("RECAPTCHA_SECRET_KEY not found in environment")
            self.secret_key = None
        
        if not self.site_key:
            logger.warning("RECAPTCHA_SITE_KEY not found in environment")
            self.site_key = None
        
        self.verify_url = "https://www.google.com/recaptcha/api/siteverify"
        self.session = None
        
        # Cache TTL settings
        self.result_cache_ttl = 300  # 5 minutes for verification results
        self.policy_cache_ttl = 3600  # 1 hour for security policies
        
        # Define security policies for different actions
        self.policies = {
            'submit_planning': SecurityPolicy(
                action='submit_planning',
                min_score=0.7,
                description='Planning application submission',
                block_threshold=0.3,
                suspicious_threshold=0.5
            ),
            'contact_form': SecurityPolicy(
                action='contact_form',
                min_score=0.6,
                description='Contact form submission',
                block_threshold=0.2,
                suspicious_threshold=0.4
            ),
            'login': SecurityPolicy(
                action='login',
                min_score=0.5,
                description='User login attempt',
                block_threshold=0.2,
                suspicious_threshold=0.3
            ),
            'register': SecurityPolicy(
                action='register',
                min_score=0.6,
                description='User registration',
                block_threshold=0.3,
                suspicious_threshold=0.4
            ),
            'payment': SecurityPolicy(
                action='payment',
                min_score=0.8,
                description='Payment processing',
                block_threshold=0.4,
                suspicious_threshold=0.6
            ),
            'api_access': SecurityPolicy(
                action='api_access',
                min_score=0.7,
                description='API endpoint access',
                block_threshold=0.3,
                suspicious_threshold=0.5
            ),
            'document_upload': SecurityPolicy(
                action='document_upload',
                min_score=0.6,
                description='Document upload',
                block_threshold=0.2,
                suspicious_threshold=0.4
            ),
            'search': SecurityPolicy(
                action='search',
                min_score=0.5,
                description='Search queries',
                block_threshold=0.1,
                suspicious_threshold=0.3
            )
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_cache_key(self, token: str, remote_ip: str) -> str:
        """Generate cache key for verification result"""
        combined = f"{token}:{remote_ip}"
        return f"recaptcha:{hashlib.md5(combined.encode()).hexdigest()}"
    
    async def verify_token(self, token: str, remote_ip: str, action: str = None) -> Dict[str, Any]:
        """Verify reCAPTCHA token with Google API"""
        if not self.secret_key:
            logger.warning("reCAPTCHA not configured - allowing request")
            return {
                'success': True,
                'score': 0.9,
                'action': action or 'unknown',
                'verification_status': 'bypass_not_configured',
                'security_decision': {
                    'action': 'allow',
                    'level': 'bypass',
                    'message': 'reCAPTCHA not configured'
                }
            }
        
        if not token:
            return {
                'success': False,
                'score': 0.0,
                'action': action or 'unknown',
                'error': 'missing_token',
                'verification_status': 'failed',
                'security_decision': {
                    'action': 'block',
                    'level': 'high_risk',
                    'message': 'Missing reCAPTCHA token'
                }
            }
        
        # Check cache first
        cache_key = self._get_cache_key(token, remote_ip)
        
        if cache_manager:
            try:
                cached_result = await cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"reCAPTCHA cache hit for action: {action}")
                    cached_result['cache_status'] = 'hit'
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
        
        # Prepare verification request
        session = await self._get_session()
        data = {
            'secret': self.secret_key,
            'response': token,
            'remoteip': remote_ip
        }
        
        try:
            async with session.post(self.verify_url, data=data) as response:
                if response.status != 200:
                    logger.error(f"reCAPTCHA API error: {response.status}")
                    return {
                        'success': False,
                        'score': 0.0,
                        'action': action or 'unknown',
                        'error': 'api_error',
                        'verification_status': 'failed',
                        'security_decision': {
                            'action': 'block',
                            'level': 'high_risk',
                            'message': 'reCAPTCHA verification failed'
                        }
                    }
                
                api_result = await response.json()
                recaptcha_response = ReCAPTCHAResponse.from_api_response(api_result)
                
                # Apply security policy
                policy = self.policies.get(action, self.policies['api_access'])
                security_decision = policy.evaluate(recaptcha_response.score)
                
                result = {
                    'success': recaptcha_response.success,
                    'score': recaptcha_response.score,
                    'action': recaptcha_response.action or action or 'unknown',
                    'challenge_ts': recaptcha_response.challenge_ts,
                    'hostname': recaptcha_response.hostname,
                    'error_codes': recaptcha_response.error_codes,
                    'verification_status': 'success' if recaptcha_response.success else 'failed',
                    'security_decision': security_decision,
                    'policy_applied': policy.action,
                    'cache_status': 'miss'
                }
                
                # Cache successful verifications
                if cache_manager and recaptcha_response.success:
                    try:
                        await cache_manager.set(cache_key, result, ttl=self.result_cache_ttl)
                        logger.info(f"Cached reCAPTCHA result for action: {action}")
                    except Exception as e:
                        logger.warning(f"Cache write failed: {e}")
                
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"reCAPTCHA request failed: {e}")
            return {
                'success': False,
                'score': 0.0,
                'action': action or 'unknown',
                'error': 'network_error',
                'verification_status': 'failed',
                'security_decision': {
                    'action': 'block',
                    'level': 'high_risk',
                    'message': 'Unable to verify reCAPTCHA'
                }
            }
        except Exception as e:
            logger.error(f"reCAPTCHA verification failed: {e}")
            return {
                'success': False,
                'score': 0.0,
                'action': action or 'unknown',
                'error': 'verification_error',
                'verification_status': 'failed',
                'security_decision': {
                    'action': 'block',
                    'level': 'high_risk',
                    'message': 'reCAPTCHA verification error'
                }
            }
    
    async def verify_and_enforce(self, token: str, remote_ip: str, action: str = None) -> Dict[str, Any]:
        """Verify token and return enforcement decision"""
        result = await self.verify_token(token, remote_ip, action)
        
        # Extract security decision
        security_decision = result.get('security_decision', {})
        decision_action = security_decision.get('action', 'block')
        
        # Add enforcement details
        result['enforcement'] = {
            'allow_request': decision_action == 'allow',
            'require_challenge': decision_action == 'challenge',
            'block_request': decision_action == 'block',
            'monitor_only': decision_action == 'monitor',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return result
    
    def get_site_key(self) -> Optional[str]:
        """Get public site key for frontend"""
        return self.site_key
    
    def get_security_policies(self) -> Dict[str, Dict[str, Any]]:
        """Get all security policies"""
        return {
            action: {
                'min_score': policy.min_score,
                'description': policy.description,
                'block_threshold': policy.block_threshold,
                'suspicious_threshold': policy.suspicious_threshold
            }
            for action, policy in self.policies.items()
        }
    
    async def update_security_policy(self, action: str, min_score: float, block_threshold: float = None, suspicious_threshold: float = None) -> bool:
        """Update security policy for an action"""
        if action not in self.policies:
            return False
        
        policy = self.policies[action]
        policy.min_score = min_score
        
        if block_threshold is not None:
            policy.block_threshold = block_threshold
        
        if suspicious_threshold is not None:
            policy.suspicious_threshold = suspicious_threshold
        
        logger.info(f"Updated security policy for {action}: min_score={min_score}")
        return True

# Initialize service
recaptcha_service = ReCAPTCHAService()

# API Router
router = APIRouter(prefix="/api/recaptcha", tags=["reCAPTCHA"])

@router.post("/verify")
async def verify_recaptcha(
    token: str = Body(..., description="reCAPTCHA token"),
    action: str = Body(None, description="Action being verified"),
    remote_ip: str = Body(..., description="Client IP address")
):
    """Verify reCAPTCHA token and return security decision"""
    try:
        result = await recaptcha_service.verify_and_enforce(token, remote_ip, action)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"reCAPTCHA verification endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/site-key")
async def get_site_key():
    """Get reCAPTCHA site key for frontend"""
    try:
        site_key = recaptcha_service.get_site_key()
        return {
            'site_key': site_key,
            'configured': site_key is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get site key endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/policies")
async def get_security_policies():
    """Get all security policies"""
    try:
        policies = recaptcha_service.get_security_policies()
        return {
            'policies': policies,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get policies endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/policies/{action}")
async def update_security_policy(
    action: str,
    min_score: float = Body(..., description="Minimum score required", ge=0.0, le=1.0),
    block_threshold: float = Body(None, description="Score below which to block", ge=0.0, le=1.0),
    suspicious_threshold: float = Body(None, description="Score below which to flag", ge=0.0, le=1.0)
):
    """Update security policy for an action"""
    try:
        updated = await recaptcha_service.update_security_policy(
            action, min_score, block_threshold, suspicious_threshold
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Action not found")
        
        return {
            'action': action,
            'updated': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update policy endpoint failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/health")
async def health_check():
    """Health check for reCAPTCHA integration"""
    return {
        "service": "recaptcha",
        "status": "healthy" if recaptcha_service.secret_key else "missing_secret_key",
        "configured": recaptcha_service.secret_key is not None and recaptcha_service.site_key is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

# Cleanup handler
async def cleanup_recaptcha():
    """Cleanup reCAPTCHA service resources"""
    await recaptcha_service.close()

# Helper function for middleware integration
async def verify_recaptcha_middleware(token: str, remote_ip: str, action: str = None) -> Dict[str, Any]:
    """Helper for middleware integration"""
    return await recaptcha_service.verify_and_enforce(token, remote_ip, action)