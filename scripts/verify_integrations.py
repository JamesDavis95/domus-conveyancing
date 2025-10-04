#!/usr/bin/env python3
"""
Integration Verification Script

Tests all API integrations to ensure they're working correctly:
- Environment configuration validation
- Stripe billing system verification
- OpenAI Planning AI testing
- SendGrid email service validation
- EPC energy certificates testing
- Companies House API verification
- reCAPTCHA protection testing
- Public data sources validation

Run this script to verify all integrations are properly configured.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationVerifier:
    """Comprehensive integration verification"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'base_url': base_url,
            'environment': {},
            'integrations': {},
            'overall_status': 'unknown'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Verify all required environment variables are set"""
        logger.info("🔍 Checking environment variables...")
        
        # Server-side secrets (should be set)
        server_vars = {
            'STRIPE_SECRET_KEY': os.getenv('STRIPE_SECRET_KEY'),
            'STRIPE_WEBHOOK_SECRET': os.getenv('STRIPE_WEBHOOK_SECRET'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'SENDGRID_API_KEY': os.getenv('SENDGRID_API_KEY'),
            'EPC_AUTH_BASIC': os.getenv('EPC_AUTH_BASIC'),
            'COMPANIES_HOUSE_API_KEY': os.getenv('COMPANIES_HOUSE_API_KEY'),
            'RECAPTCHA_SECRET_KEY': os.getenv('RECAPTCHA_SECRET_KEY')
        }
        
        # Browser-safe keys (should be set)
        browser_vars = {
            'STRIPE_PUBLISHABLE_KEY': os.getenv('STRIPE_PUBLISHABLE_KEY'),
            'MAPBOX_ACCESS_TOKEN': os.getenv('MAPBOX_ACCESS_TOKEN'),
            'RECAPTCHA_SITE_KEY': os.getenv('RECAPTCHA_SITE_KEY')
        }
        
        # API endpoints
        endpoint_vars = {
            'EA_FLOOD_API_URL': os.getenv('EA_FLOOD_API_URL'),
            'PLANIT_API_URL': os.getenv('PLANIT_API_URL'),
            'PDG_API_URL': os.getenv('PDG_API_URL')
        }
        
        results = {
            'server_secrets': {},
            'browser_keys': {},
            'api_endpoints': {},
            'missing_critical': [],
            'status': 'pass'
        }
        
        # Check server secrets
        for var, value in server_vars.items():
            is_set = bool(value and len(value.strip()) > 0)
            results['server_secrets'][var] = {
                'set': is_set,
                'length': len(value) if value else 0,
                'preview': f"{value[:8]}..." if value and len(value) > 8 else None
            }
            if not is_set and var in ['STRIPE_SECRET_KEY', 'OPENAI_API_KEY']:
                results['missing_critical'].append(var)
        
        # Check browser keys
        for var, value in browser_vars.items():
            is_set = bool(value and len(value.strip()) > 0)
            results['browser_keys'][var] = {
                'set': is_set,
                'length': len(value) if value else 0,
                'preview': f"{value[:8]}..." if value and len(value) > 8 else None
            }
        
        # Check endpoints
        for var, value in endpoint_vars.items():
            is_set = bool(value and len(value.strip()) > 0)
            results['api_endpoints'][var] = {
                'set': is_set,
                'url': value if value else None
            }
        
        if results['missing_critical']:
            results['status'] = 'fail'
            logger.error(f"❌ Missing critical environment variables: {results['missing_critical']}")
        else:
            logger.info("✅ Environment variables check passed")
        
        return results
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test all integration health endpoints"""
        logger.info("🔍 Testing health endpoints...")
        
        health_endpoints = [
            '/api/stripe/health',
            '/api/openai/health', 
            '/api/email/health',
            '/api/epc/health',
            '/api/companies-house/health',
            '/api/recaptcha/health',
            '/api/public-data/health'
        ]
        
        results = {
            'endpoints': {},
            'healthy_count': 0,
            'total_count': len(health_endpoints),
            'status': 'pass'
        }
        
        for endpoint in health_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        results['endpoints'][endpoint] = {
                            'status': 'healthy',
                            'response_time': response.headers.get('X-Response-Time'),
                            'service_status': data.get('status', 'unknown'),
                            'configured': data.get('configured', True)
                        }
                        results['healthy_count'] += 1
                        logger.info(f"✅ {endpoint} - healthy")
                    else:
                        results['endpoints'][endpoint] = {
                            'status': 'unhealthy',
                            'status_code': response.status,
                            'error': f"HTTP {response.status}"
                        }
                        logger.warning(f"⚠️ {endpoint} - unhealthy (HTTP {response.status})")
            except Exception as e:
                results['endpoints'][endpoint] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"❌ {endpoint} - error: {e}")
        
        if results['healthy_count'] < results['total_count']:
            results['status'] = 'partial'
        
        logger.info(f"Health check: {results['healthy_count']}/{results['total_count']} endpoints healthy")
        return results
    
    async def test_stripe_integration(self) -> Dict[str, Any]:
        """Test Stripe billing integration"""
        logger.info("🔍 Testing Stripe integration...")
        
        results = {
            'plans_fetch': False,
            'checkout_validation': False,
            'webhook_endpoint': False,
            'status': 'fail'
        }
        
        try:
            # Test plans endpoint
            url = f"{self.base_url}/api/stripe/plans"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'plans' in data:
                        results['plans_fetch'] = True
                        logger.info("✅ Stripe plans fetch successful")
                    else:
                        logger.warning("⚠️ Stripe plans response missing 'plans' key")
                else:
                    logger.error(f"❌ Stripe plans fetch failed: HTTP {response.status}")
            
            # Test webhook endpoint exists
            url = f"{self.base_url}/api/stripe/webhook"
            async with self.session.post(url, json={}) as response:
                # Expect 400/422 for invalid webhook, not 404
                if response.status in [400, 422, 500]:
                    results['webhook_endpoint'] = True
                    logger.info("✅ Stripe webhook endpoint exists")
                elif response.status == 404:
                    logger.error("❌ Stripe webhook endpoint not found")
                else:
                    logger.warning(f"⚠️ Stripe webhook unexpected response: HTTP {response.status}")
            
            if results['plans_fetch'] and results['webhook_endpoint']:
                results['status'] = 'pass'
            
        except Exception as e:
            logger.error(f"❌ Stripe integration test failed: {e}")
        
        return results
    
    async def test_openai_integration(self) -> Dict[str, Any]:
        """Test OpenAI Planning AI integration"""
        logger.info("🔍 Testing OpenAI integration...")
        
        results = {
            'models_list': False,
            'analysis_endpoint': False,
            'credit_enforcement': False,
            'status': 'fail'
        }
        
        try:
            # Test models endpoint
            url = f"{self.base_url}/api/openai/models"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'models' in data:
                        results['models_list'] = True
                        logger.info("✅ OpenAI models list successful")
                else:
                    logger.error(f"❌ OpenAI models fetch failed: HTTP {response.status}")
            
            # Test analysis endpoint (should require auth/credits)
            url = f"{self.base_url}/api/openai/planning-analysis"
            test_data = {
                'description': 'Test planning application for integration verification',
                'location': 'Test Location'
            }
            async with self.session.post(url, json=test_data) as response:
                # Expect 401 (unauthorized) or 402 (insufficient credits)
                if response.status in [401, 402, 422]:
                    results['analysis_endpoint'] = True
                    results['credit_enforcement'] = True
                    logger.info("✅ OpenAI analysis endpoint exists with proper auth")
                elif response.status == 200:
                    # Unexpected success - might indicate missing auth
                    logger.warning("⚠️ OpenAI analysis succeeded without auth (potential security issue)")
                else:
                    logger.error(f"❌ OpenAI analysis unexpected response: HTTP {response.status}")
            
            if results['models_list'] and results['analysis_endpoint']:
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ OpenAI integration test failed: {e}")
        
        return results
    
    async def test_email_integration(self) -> Dict[str, Any]:
        """Test SendGrid email integration"""
        logger.info("🔍 Testing SendGrid email integration...")
        
        results = {
            'send_endpoint': False,
            'templates_list': False,
            'validation': False,
            'status': 'fail'
        }
        
        try:
            # Test templates endpoint
            url = f"{self.base_url}/api/email/templates"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'templates' in data:
                        results['templates_list'] = True
                        logger.info("✅ Email templates list successful")
                else:
                    logger.warning(f"⚠️ Email templates fetch failed: HTTP {response.status}")
            
            # Test send endpoint (should validate input)
            url = f"{self.base_url}/api/email/send"
            test_data = {
                'to': 'invalid-email',  # Invalid email to test validation
                'template': 'test'
            }
            async with self.session.post(url, json=test_data) as response:
                # Expect 400/422 for validation error
                if response.status in [400, 422]:
                    results['send_endpoint'] = True
                    results['validation'] = True
                    logger.info("✅ Email send endpoint exists with validation")
                elif response.status == 401:
                    results['send_endpoint'] = True
                    logger.info("✅ Email send endpoint exists (requires auth)")
                else:
                    logger.warning(f"⚠️ Email send unexpected response: HTTP {response.status}")
            
            if results['templates_list'] and results['send_endpoint']:
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ Email integration test failed: {e}")
        
        return results
    
    async def test_epc_integration(self) -> Dict[str, Any]:
        """Test EPC energy certificates integration"""
        logger.info("🔍 Testing EPC integration...")
        
        results = {
            'search_endpoint': False,
            'postcode_search': False,
            'auth_protection': False,
            'status': 'fail'
        }
        
        try:
            # Test search by postcode
            url = f"{self.base_url}/api/epc/search/postcode/SW1A1AA"
            async with self.session.get(url) as response:
                if response.status in [200, 404]:  # 404 acceptable for test postcode
                    results['search_endpoint'] = True
                    results['postcode_search'] = True
                    logger.info("✅ EPC postcode search endpoint working")
                elif response.status == 401:
                    results['auth_protection'] = True
                    logger.info("✅ EPC endpoint has auth protection")
                else:
                    logger.warning(f"⚠️ EPC search unexpected response: HTTP {response.status}")
            
            if results['search_endpoint'] or results['auth_protection']:
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ EPC integration test failed: {e}")
        
        return results
    
    async def test_companies_house_integration(self) -> Dict[str, Any]:
        """Test Companies House integration"""
        logger.info("🔍 Testing Companies House integration...")
        
        results = {
            'search_endpoint': False,
            'company_lookup': False,
            'rate_limiting': False,
            'status': 'fail'
        }
        
        try:
            # Test company search
            url = f"{self.base_url}/api/companies-house/search"
            params = {'q': 'test company'}
            async with self.session.get(url, params=params) as response:
                if response.status in [200, 400]:  # 400 acceptable for validation
                    results['search_endpoint'] = True
                    logger.info("✅ Companies House search endpoint working")
                else:
                    logger.warning(f"⚠️ Companies House search response: HTTP {response.status}")
            
            # Test company details lookup
            url = f"{self.base_url}/api/companies-house/company/00000000"
            async with self.session.get(url) as response:
                if response.status in [200, 404]:  # 404 expected for fake company number
                    results['company_lookup'] = True
                    logger.info("✅ Companies House company lookup working")
                else:
                    logger.warning(f"⚠️ Companies House lookup response: HTTP {response.status}")
            
            if results['search_endpoint'] and results['company_lookup']:
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ Companies House integration test failed: {e}")
        
        return results
    
    async def test_recaptcha_integration(self) -> Dict[str, Any]:
        """Test reCAPTCHA integration"""
        logger.info("🔍 Testing reCAPTCHA integration...")
        
        results = {
            'site_key_endpoint': False,
            'verify_endpoint': False,
            'policies_endpoint': False,
            'status': 'fail'
        }
        
        try:
            # Test site key endpoint
            url = f"{self.base_url}/api/recaptcha/site-key"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'site_key' in data:
                        results['site_key_endpoint'] = True
                        logger.info("✅ reCAPTCHA site key endpoint working")
                else:
                    logger.warning(f"⚠️ reCAPTCHA site key response: HTTP {response.status}")
            
            # Test verify endpoint
            url = f"{self.base_url}/api/recaptcha/verify"
            test_data = {
                'token': 'invalid-token',
                'remote_ip': '127.0.0.1'
            }
            async with self.session.post(url, json=test_data) as response:
                if response.status in [200, 400]:  # Should handle invalid token
                    results['verify_endpoint'] = True
                    logger.info("✅ reCAPTCHA verify endpoint working")
                else:
                    logger.warning(f"⚠️ reCAPTCHA verify response: HTTP {response.status}")
            
            # Test policies endpoint
            url = f"{self.base_url}/api/recaptcha/policies"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'policies' in data:
                        results['policies_endpoint'] = True
                        logger.info("✅ reCAPTCHA policies endpoint working")
                else:
                    logger.warning(f"⚠️ reCAPTCHA policies response: HTTP {response.status}")
            
            if all([results['site_key_endpoint'], results['verify_endpoint'], results['policies_endpoint']]):
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ reCAPTCHA integration test failed: {e}")
        
        return results
    
    async def test_public_data_integration(self) -> Dict[str, Any]:
        """Test public data sources integration"""
        logger.info("🔍 Testing public data integration...")
        
        results = {
            'flood_risk_endpoint': False,
            'planning_search': False,
            'commercial_properties': False,
            'area_insights': False,
            'status': 'fail'
        }
        
        try:
            # Test flood risk endpoint
            url = f"{self.base_url}/api/public-data/flood-risk/SW1A1AA"
            async with self.session.get(url) as response:
                if response.status in [200, 404]:
                    results['flood_risk_endpoint'] = True
                    logger.info("✅ Flood risk endpoint working")
                else:
                    logger.warning(f"⚠️ Flood risk response: HTTP {response.status}")
            
            # Test planning applications search
            url = f"{self.base_url}/api/public-data/planning-applications"
            params = {'postcode': 'SW1A1AA'}
            async with self.session.get(url, params=params) as response:
                if response.status in [200, 400]:
                    results['planning_search'] = True
                    logger.info("✅ Planning applications search working")
                else:
                    logger.warning(f"⚠️ Planning search response: HTTP {response.status}")
            
            # Test commercial properties
            url = f"{self.base_url}/api/public-data/commercial-properties"
            params = {'postcode': 'SW1A1AA'}
            async with self.session.get(url, params=params) as response:
                if response.status in [200, 400]:
                    results['commercial_properties'] = True
                    logger.info("✅ Commercial properties search working")
                else:
                    logger.warning(f"⚠️ Commercial properties response: HTTP {response.status}")
            
            # Test area insights
            url = f"{self.base_url}/api/public-data/area-insights/SW1A1AA"
            async with self.session.get(url) as response:
                if response.status in [200, 404]:
                    results['area_insights'] = True
                    logger.info("✅ Area insights endpoint working")
                else:
                    logger.warning(f"⚠️ Area insights response: HTTP {response.status}")
            
            working_endpoints = sum([
                results['flood_risk_endpoint'],
                results['planning_search'], 
                results['commercial_properties'],
                results['area_insights']
            ])
            
            if working_endpoints >= 3:  # At least 3 out of 4 working
                results['status'] = 'pass'
                
        except Exception as e:
            logger.error(f"❌ Public data integration test failed: {e}")
        
        return results
    
    async def run_verification(self) -> Dict[str, Any]:
        """Run complete integration verification"""
        logger.info("🚀 Starting comprehensive integration verification...")
        
        # Check environment variables first
        self.results['environment'] = self.check_environment_variables()
        
        if self.results['environment']['status'] == 'fail':
            logger.error("❌ Environment check failed - skipping API tests")
            self.results['overall_status'] = 'fail'
            return self.results
        
        # Test all integrations
        integration_tests = [
            ('health_endpoints', self.test_health_endpoints()),
            ('stripe', self.test_stripe_integration()),
            ('openai', self.test_openai_integration()),
            ('email', self.test_email_integration()),
            ('epc', self.test_epc_integration()),
            ('companies_house', self.test_companies_house_integration()),
            ('recaptcha', self.test_recaptcha_integration()),
            ('public_data', self.test_public_data_integration())
        ]
        
        for test_name, test_coro in integration_tests:
            try:
                self.results['integrations'][test_name] = await test_coro
            except Exception as e:
                logger.error(f"❌ {test_name} test failed with exception: {e}")
                self.results['integrations'][test_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Calculate overall status
        passed_tests = sum(1 for result in self.results['integrations'].values() 
                          if result.get('status') == 'pass')
        total_tests = len(self.results['integrations'])
        
        if passed_tests == total_tests:
            self.results['overall_status'] = 'pass'
            logger.info(f"✅ All integrations verified successfully ({passed_tests}/{total_tests})")
        elif passed_tests >= total_tests * 0.75:  # 75% pass rate
            self.results['overall_status'] = 'partial'
            logger.warning(f"⚠️ Most integrations working ({passed_tests}/{total_tests})")
        else:
            self.results['overall_status'] = 'fail'
            logger.error(f"❌ Many integrations failing ({passed_tests}/{total_tests})")
        
        return self.results
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*80)
        print("🔍 DOMUS API INTEGRATION VERIFICATION SUMMARY")
        print("="*80)
        
        # Environment status
        env_status = self.results['environment']['status']
        env_icon = "✅" if env_status == 'pass' else "❌"
        print(f"\n{env_icon} Environment Configuration: {env_status.upper()}")
        
        if self.results['environment']['missing_critical']:
            print(f"   Missing critical variables: {self.results['environment']['missing_critical']}")
        
        # Integration status
        print(f"\n🔗 Integration Test Results:")
        for name, result in self.results['integrations'].items():
            status = result.get('status', 'unknown')
            icon = "✅" if status == 'pass' else "⚠️" if status == 'partial' else "❌"
            print(f"   {icon} {name.replace('_', ' ').title()}: {status.upper()}")
            
            if 'error' in result:
                print(f"      Error: {result['error']}")
        
        # Overall status
        overall = self.results['overall_status']
        overall_icon = "✅" if overall == 'pass' else "⚠️" if overall == 'partial' else "❌"
        print(f"\n{overall_icon} Overall Status: {overall.upper()}")
        
        print("\n" + "="*80)
        print(f"Verification completed at: {self.results['timestamp']}")
        print("="*80)

async def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Domus API integrations')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Base URL for API testing (default: http://localhost:8000)')
    parser.add_argument('--output', help='Save results to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    async with IntegrationVerifier(args.url) as verifier:
        results = await verifier.run_verification()
        verifier.print_summary()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")
        
        # Exit with appropriate code
        overall_status = results['overall_status']
        if overall_status == 'pass':
            sys.exit(0)
        elif overall_status == 'partial':
            sys.exit(1)
        else:
            sys.exit(2)

if __name__ == '__main__':
    asyncio.run(main())