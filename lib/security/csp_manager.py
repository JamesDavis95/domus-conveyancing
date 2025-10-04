"""
Content Security Policy (CSP) Manager
Implements comprehensive CSP headers for XSS protection
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CSPManager:
    """Content Security Policy manager for XSS protection"""
    
    def __init__(self):
        # CSP policies for different environments
        self.policies = {
            'strict': self._get_strict_policy(),
            'development': self._get_development_policy(),
            'production': self._get_production_policy()
        }
    
    def _get_strict_policy(self) -> Dict[str, List[str]]:
        """Strict CSP policy for maximum security"""
        return {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",  # Required for inline scripts (minimize in production)
                "https://js.stripe.com",  # Stripe payments
                "https://www.google.com",  # reCAPTCHA (if implemented)
                "https://www.gstatic.com"  # Google fonts/services
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",  # Required for CSS frameworks
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net"  # CSS libraries
            ],
            'font-src': [
                "'self'",
                "https://fonts.gstatic.com",
                "data:"  # For base64 encoded fonts
            ],
            'img-src': [
                "'self'",
                "data:",  # For base64 images
                "https:",  # Allow HTTPS images
                "*.domus.conveyancing",  # Subdomains
                "https://via.placeholder.com"  # Placeholder images
            ],
            'connect-src': [
                "'self'",
                "https://api.stripe.com",  # Stripe API
                "wss:",  # WebSocket connections
                "https:"  # API endpoints
            ],
            'frame-src': [
                "'self'",
                "https://js.stripe.com",  # Stripe payment frames
                "https://hooks.stripe.com"  # Stripe webhooks
            ],
            'object-src': ["'none'"],  # Disable plugins
            'base-uri': ["'self'"],  # Restrict base URI
            'form-action': ["'self'"],  # Restrict form submissions
            'frame-ancestors': ["'none'"],  # Prevent framing (clickjacking)
            'upgrade-insecure-requests': [],  # Upgrade HTTP to HTTPS
            'block-all-mixed-content': []  # Block mixed content
        }
    
    def _get_development_policy(self) -> Dict[str, List[str]]:
        """Relaxed CSP policy for development"""
        return {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'unsafe-inline'",
                "'unsafe-eval'",  # Allow eval for development
                "https://js.stripe.com",
                "http://localhost:*",  # Local development
                "ws://localhost:*"  # WebSocket for hot reload
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net"
            ],
            'font-src': [
                "'self'",
                "https://fonts.gstatic.com",
                "data:"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "http://localhost:*"
            ],
            'connect-src': [
                "'self'",
                "https://api.stripe.com",
                "ws:",
                "wss:",
                "http://localhost:*",
                "https:"
            ],
            'frame-src': [
                "'self'",
                "https://js.stripe.com"
            ],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"]
        }
    
    def _get_production_policy(self) -> Dict[str, List[str]]:
        """Production CSP policy balancing security and functionality"""
        return {
            'default-src': ["'self'"],
            'script-src': [
                "'self'",
                "'nonce-{nonce}'",  # Use nonces for inline scripts
                "https://js.stripe.com",
                "https://www.google.com",
                "https://www.gstatic.com"
            ],
            'style-src': [
                "'self'",
                "'nonce-{nonce}'",  # Use nonces for inline styles
                "https://fonts.googleapis.com",
                "https://cdn.jsdelivr.net"
            ],
            'font-src': [
                "'self'",
                "https://fonts.gstatic.com",
                "data:"
            ],
            'img-src': [
                "'self'",
                "data:",
                "https:",
                "*.domus.conveyancing"
            ],
            'connect-src': [
                "'self'",
                "https://api.stripe.com",
                "wss://domus.conveyancing",
                "https:"
            ],
            'frame-src': [
                "'self'",
                "https://js.stripe.com",
                "https://hooks.stripe.com"
            ],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'none'"],
            'upgrade-insecure-requests': [],
            'block-all-mixed-content': []
        }
    
    def generate_nonce(self) -> str:
        """Generate cryptographic nonce for CSP"""
        import secrets
        return secrets.token_urlsafe(16)
    
    def build_csp_header(self, policy_name: str = 'production', nonce: str = None) -> str:
        """Build CSP header string"""
        
        if policy_name not in self.policies:
            policy_name = 'production'
        
        policy = self.policies[policy_name].copy()
        
        # Replace nonce placeholder if provided
        if nonce:
            for directive, sources in policy.items():
                policy[directive] = [
                    source.replace('{nonce}', nonce) if '{nonce}' in source else source
                    for source in sources
                ]
        
        # Build CSP string
        csp_parts = []
        for directive, sources in policy.items():
            if sources:
                csp_parts.append(f"{directive} {' '.join(sources)}")
            else:
                csp_parts.append(directive)
        
        return '; '.join(csp_parts)
    
    def get_security_headers(self, environment: str = 'production', nonce: str = None) -> Dict[str, str]:
        """Get comprehensive security headers"""
        
        headers = {
            'Content-Security-Policy': self.build_csp_header(environment, nonce),
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload'
        }
        
        if environment == 'development':
            # Relax some headers for development
            headers['X-Frame-Options'] = 'SAMEORIGIN'
            headers.pop('Strict-Transport-Security', None)  # Remove HSTS for HTTP
        
        return headers
    
    def validate_csp_report(self, report: Dict) -> Dict:
        """Validate and process CSP violation report"""
        
        required_fields = ['document-uri', 'violated-directive', 'blocked-uri']
        
        if not all(field in report for field in required_fields):
            return {
                'valid': False,
                'error': 'Missing required CSP report fields'
            }
        
        # Extract key information
        violation = {
            'document_uri': report['document-uri'],
            'violated_directive': report['violated-directive'],
            'blocked_uri': report['blocked-uri'],
            'source_file': report.get('source-file'),
            'line_number': report.get('line-number'),
            'column_number': report.get('column-number'),
            'original_policy': report.get('original-policy')
        }
        
        # Categorize violation
        directive = violation['violated_directive'].split()[0]
        violation['category'] = self._categorize_violation(directive)
        violation['severity'] = self._assess_severity(violation)
        
        logger.warning(f"CSP violation: {violation['violated_directive']} - {violation['blocked_uri']}")
        
        return {
            'valid': True,
            'violation': violation
        }
    
    def _categorize_violation(self, directive: str) -> str:
        """Categorize CSP violation by directive"""
        
        categories = {
            'script-src': 'script_injection',
            'style-src': 'style_injection', 
            'img-src': 'image_loading',
            'connect-src': 'ajax_request',
            'frame-src': 'iframe_loading',
            'object-src': 'plugin_loading',
            'font-src': 'font_loading',
            'media-src': 'media_loading'
        }
        
        return categories.get(directive, 'unknown')
    
    def _assess_severity(self, violation: Dict) -> str:
        """Assess severity of CSP violation"""
        
        blocked_uri = violation['blocked_uri']
        directive = violation['violated_directive']
        
        # High severity indicators
        if 'javascript:' in blocked_uri or 'data:' in blocked_uri:
            return 'high'
        
        if 'script-src' in directive and ('eval' in blocked_uri or 'inline' in directive):
            return 'high'
        
        # Medium severity
        if 'script-src' in directive or 'style-src' in directive:
            return 'medium'
        
        # Low severity
        return 'low'

class CSPMiddleware:
    """Middleware to add CSP headers to responses"""
    
    def __init__(self, environment: str = 'production'):
        self.csp_manager = CSPManager()
        self.environment = environment
    
    def add_security_headers(self, response, nonce: str = None):
        """Add security headers to response"""
        
        headers = self.csp_manager.get_security_headers(self.environment, nonce)
        
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
        
        return response
    
    def generate_nonce_for_request(self):
        """Generate nonce for current request"""
        return self.csp_manager.generate_nonce()