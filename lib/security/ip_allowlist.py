"""
IP Allowlist System
Optional IP allowlist for admin access and sensitive operations
"""

import ipaddress
from typing import List, Optional, Set, Dict, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

@dataclass
class IPRule:
    """IP allowlist rule"""
    
    network: str
    description: str
    rule_type: str  # 'allow', 'deny', 'admin_only'
    created_at: datetime
    expires_at: Optional[datetime] = None
    created_by: Optional[str] = None

class IPAllowlist:
    """IP allowlist management system"""
    
    def __init__(self, enable_allowlist: bool = False):
        self.enabled = enable_allowlist
        self.rules: List[IPRule] = []
        self.admin_networks: Set[ipaddress.IPv4Network] = set()
        self.blocked_networks: Set[ipaddress.IPv4Network] = set()
        self.allowed_networks: Set[ipaddress.IPv4Network] = set()
        self.logger = logging.getLogger('ip_allowlist')
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default IP allowlist rules"""
        
        # Default safe networks (private ranges)
        default_rules = [
            {
                'network': '127.0.0.0/8',
                'description': 'Loopback addresses',
                'rule_type': 'allow'
            },
            {
                'network': '192.168.0.0/16',
                'description': 'Private network range',
                'rule_type': 'allow'
            },
            {
                'network': '10.0.0.0/8',
                'description': 'Private network range',
                'rule_type': 'allow'
            },
            {
                'network': '172.16.0.0/12',
                'description': 'Private network range',
                'rule_type': 'allow'
            }
        ]
        
        for rule_data in default_rules:
            self.add_rule(
                network=rule_data['network'],
                description=rule_data['description'],
                rule_type=rule_data['rule_type']
            )
    
    def add_rule(self, network: str, description: str, rule_type: str = 'allow',
                 expires_in_days: Optional[int] = None, created_by: Optional[str] = None) -> bool:
        """Add IP allowlist rule"""
        
        try:
            # Validate network
            ip_network = ipaddress.ip_network(network, strict=False)
            
            # Calculate expiry
            expires_at = None
            if expires_in_days:
                expires_at = datetime.now() + timedelta(days=expires_in_days)
            
            # Create rule
            rule = IPRule(
                network=str(ip_network),
                description=description,
                rule_type=rule_type,
                created_at=datetime.now(),
                expires_at=expires_at,
                created_by=created_by
            )
            
            self.rules.append(rule)
            
            # Update internal sets
            if rule_type == 'allow':
                self.allowed_networks.add(ip_network)
            elif rule_type == 'deny':
                self.blocked_networks.add(ip_network)
            elif rule_type == 'admin_only':
                self.admin_networks.add(ip_network)
            
            self.logger.info(f"Added IP rule: {network} ({rule_type}) - {description}")
            return True
            
        except ValueError as e:
            self.logger.error(f"Invalid IP network: {network} - {e}")
            return False
    
    def remove_rule(self, network: str) -> bool:
        """Remove IP allowlist rule"""
        
        try:
            ip_network = ipaddress.ip_network(network, strict=False)
            
            # Find and remove rule
            for i, rule in enumerate(self.rules):
                if rule.network == str(ip_network):
                    removed_rule = self.rules.pop(i)
                    
                    # Update internal sets
                    if removed_rule.rule_type == 'allow':
                        self.allowed_networks.discard(ip_network)
                    elif removed_rule.rule_type == 'deny':
                        self.blocked_networks.discard(ip_network)
                    elif removed_rule.rule_type == 'admin_only':
                        self.admin_networks.discard(ip_network)
                    
                    self.logger.info(f"Removed IP rule: {network}")
                    return True
            
            return False
            
        except ValueError as e:
            self.logger.error(f"Invalid IP network: {network} - {e}")
            return False
    
    def is_ip_allowed(self, ip_address: str, require_admin: bool = False) -> bool:
        """Check if IP address is allowed"""
        
        if not self.enabled:
            return True
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check if IP is blocked
            for network in self.blocked_networks:
                if ip in network:
                    self.logger.warning(f"Blocked IP access: {ip_address}")
                    return False
            
            # If admin access is required
            if require_admin:
                for network in self.admin_networks:
                    if ip in network:
                        return True
                
                # Check if admin access is allowed from any allowed network
                for network in self.allowed_networks:
                    if ip in network:
                        return True
                
                self.logger.warning(f"Admin access denied for IP: {ip_address}")
                return False
            
            # Check if IP is in allowed networks
            for network in self.allowed_networks:
                if ip in network:
                    return True
            
            for network in self.admin_networks:
                if ip in network:
                    return True
            
            # If allowlist is enabled but IP not found, deny
            self.logger.warning(f"IP not in allowlist: {ip_address}")
            return False
            
        except ValueError:
            self.logger.error(f"Invalid IP address: {ip_address}")
            return False
    
    def cleanup_expired_rules(self):
        """Remove expired rules"""
        
        now = datetime.now()
        expired_rules = []
        
        for i, rule in enumerate(self.rules):
            if rule.expires_at and rule.expires_at <= now:
                expired_rules.append(i)
        
        # Remove expired rules (reverse order to maintain indices)
        for i in reversed(expired_rules):
            expired_rule = self.rules.pop(i)
            
            # Update internal sets
            try:
                ip_network = ipaddress.ip_network(expired_rule.network)
                
                if expired_rule.rule_type == 'allow':
                    self.allowed_networks.discard(ip_network)
                elif expired_rule.rule_type == 'deny':
                    self.blocked_networks.discard(ip_network)
                elif expired_rule.rule_type == 'admin_only':
                    self.admin_networks.discard(ip_network)
                
                self.logger.info(f"Expired IP rule removed: {expired_rule.network}")
                
            except ValueError:
                pass
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all IP rules"""
        
        rules_data = []
        
        for rule in self.rules:
            rules_data.append({
                'network': rule.network,
                'description': rule.description,
                'rule_type': rule.rule_type,
                'created_at': rule.created_at.isoformat(),
                'expires_at': rule.expires_at.isoformat() if rule.expires_at else None,
                'created_by': rule.created_by,
                'is_expired': rule.expires_at and rule.expires_at <= datetime.now()
            })
        
        return rules_data
    
    def get_client_ip_info(self, ip_address: str) -> Dict[str, Any]:
        """Get information about client IP"""
        
        try:
            ip = ipaddress.ip_address(ip_address)
            
            info = {
                'ip_address': ip_address,
                'is_private': ip.is_private,
                'is_loopback': ip.is_loopback,
                'is_allowed': self.is_ip_allowed(ip_address),
                'admin_access_allowed': self.is_ip_allowed(ip_address, require_admin=True),
                'matching_rules': []
            }
            
            # Find matching rules
            for rule in self.rules:
                try:
                    network = ipaddress.ip_network(rule.network)
                    if ip in network:
                        info['matching_rules'].append({
                            'network': rule.network,
                            'description': rule.description,
                            'rule_type': rule.rule_type
                        })
                except ValueError:
                    continue
            
            return info
            
        except ValueError:
            return {
                'ip_address': ip_address,
                'is_valid': False,
                'error': 'Invalid IP address'
            }
    
    def enable_allowlist(self):
        """Enable IP allowlist"""
        
        self.enabled = True
        self.logger.info("IP allowlist enabled")
    
    def disable_allowlist(self):
        """Disable IP allowlist"""
        
        self.enabled = False
        self.logger.info("IP allowlist disabled")
    
    def import_rules_from_config(self, config: Dict[str, Any]):
        """Import rules from configuration"""
        
        if 'enabled' in config:
            self.enabled = config['enabled']
        
        if 'rules' in config:
            for rule_config in config['rules']:
                self.add_rule(
                    network=rule_config['network'],
                    description=rule_config.get('description', ''),
                    rule_type=rule_config.get('rule_type', 'allow'),
                    expires_in_days=rule_config.get('expires_in_days'),
                    created_by=rule_config.get('created_by')
                )
    
    def export_rules_to_config(self) -> Dict[str, Any]:
        """Export rules to configuration format"""
        
        return {
            'enabled': self.enabled,
            'rules': [
                {
                    'network': rule.network,
                    'description': rule.description,
                    'rule_type': rule.rule_type,
                    'expires_in_days': (
                        (rule.expires_at - datetime.now()).days
                        if rule.expires_at else None
                    ),
                    'created_by': rule.created_by
                }
                for rule in self.rules
            ]
        }

class IPAllowlistMiddleware:
    """FastAPI middleware for IP allowlist enforcement"""
    
    def __init__(self, allowlist: IPAllowlist):
        self.allowlist = allowlist
        self.logger = logging.getLogger('ip_allowlist_middleware')
    
    async def __call__(self, request, call_next):
        """Process request through IP allowlist"""
        
        if not self.allowlist.enabled:
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if admin endpoint
        is_admin_endpoint = self._is_admin_endpoint(request.url.path)
        
        # Check IP allowlist
        if not self.allowlist.is_ip_allowed(client_ip, require_admin=is_admin_endpoint):
            self.logger.warning(
                f"IP blocked: {client_ip} attempting to access {request.url.path}"
            )
            
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail="Access denied from this IP address"
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        
        # Check X-Forwarded-For header first (for proxies)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        return request.client.host
    
    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if endpoint requires admin access"""
        
        admin_paths = [
            '/admin/',
            '/api/admin/',
            '/api/users/admin',
            '/api/system/',
            '/api/logs/',
            '/api/metrics/'
        ]
        
        return any(path.startswith(admin_path) for admin_path in admin_paths)

# Global IP allowlist instance
ip_allowlist = IPAllowlist()