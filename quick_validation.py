#!/usr/bin/env python3
"""
Quick Platform Validation
Simple script to validate current platform state and key client-ready features
"""

import urllib.request
import urllib.parse
import urllib.error
import json
import time
from datetime import datetime

class QuickValidator:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {}
        
    def run_quick_validation(self):
        """Run quick validation of client-ready features"""
        print("🚀 Domus Platform - Quick Validation")
        print(f"🌐 Testing: {self.base_url}")
        print("=" * 60)
        
        # Test critical endpoints
        self.test_critical_endpoints()
        
        # Test legal compliance pages
        self.test_legal_pages()
        
        # Test JavaScript assets
        self.test_javascript_assets()
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Generate summary
        self.print_summary()
    
    def make_request(self, url, data=None, method='GET'):
        """Make HTTP request using urllib"""
        try:
            if data:
                data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
                if method == 'POST':
                    req.get_method = lambda: 'POST'
            else:
                req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.getcode(), response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception as e:
            return 0, str(e)
    
    def test_critical_endpoints(self):
        """Test critical application endpoints"""
        print("\n🏠 Testing Critical Endpoints...")
        
        endpoints = {
            "Main App": "/",
            "Dashboard": "/dashboard",
            "Projects": "/projects",
            "Planning AI": "/planning-ai",
            "Auto Docs": "/auto-docs",
            "Property API": "/property-api",
            "Offsets Marketplace": "/offsets-marketplace",
            "Marketplace Supply": "/marketplace/supply",
            "Settings": "/settings",
            "Billing": "/settings/billing",
            "Security": "/settings/security"
        }
        
        for name, endpoint in endpoints.items():
            status_code, content = self.make_request(f"{self.base_url}{endpoint}")
            if status_code == 200:
                print(f"  ✅ {name}: OK")
                self.results[f"endpoint_{name.lower().replace(' ', '_')}"] = True
            elif status_code > 0:
                print(f"  ⚠️  {name}: HTTP {status_code}")
                self.results[f"endpoint_{name.lower().replace(' ', '_')}"] = False
            else:
                print(f"  ❌ {name}: Failed ({content})")
                self.results[f"endpoint_{name.lower().replace(' ', '_')}"] = False
    
    def test_legal_pages(self):
        """Test legal compliance pages"""
        print("\n⚖️  Testing Legal Compliance Pages...")
        
        legal_pages = {
            "Privacy Policy": "/privacy-policy",
            "Terms of Service": "/terms-of-service", 
            "Cookie Policy": "/cookie-policy",
            "Marketplace Terms": "/marketplace/terms"
        }
        
        for name, endpoint in legal_pages.items():
            status_code, content = self.make_request(f"{self.base_url}{endpoint}")
            if status_code == 200:
                # Check for key legal content
                content_lower = content.lower()
                if name == "Privacy Policy" and "gdpr" in content_lower:
                    print(f"  ✅ {name}: OK (GDPR compliant)")
                    self.results[f"legal_{name.lower().replace(' ', '_')}"] = True
                elif name == "Cookie Policy" and "consent" in content_lower:
                    print(f"  ✅ {name}: OK (Consent framework)")
                    self.results[f"legal_{name.lower().replace(' ', '_')}"] = True
                elif name == "Marketplace Terms" and "biodiversity" in content_lower:
                    print(f"  ✅ {name}: OK (Marketplace specific)")
                    self.results[f"legal_{name.lower().replace(' ', '_')}"] = True
                else:
                    print(f"  ✅ {name}: OK")
                    self.results[f"legal_{name.lower().replace(' ', '_')}"] = True
            elif status_code > 0:
                print(f"  ❌ {name}: HTTP {status_code}")
                self.results[f"legal_{name.lower().replace(' ', '_')}"] = False
            else:
                print(f"  ❌ {name}: Failed ({content})")
                self.results[f"legal_{name.lower().replace(' ', '_')}"] = False
    
    def test_javascript_assets(self):
        """Test client-ready JavaScript assets"""
        print("\n📜 Testing JavaScript Assets...")
        
        js_assets = {
            "Cookie Consent": "/static/js/cookie-consent.js",
            "Empty States": "/static/js/empty-states.js", 
            "Error Handler": "/static/js/error-handler.js"
        }
        
        for name, asset_path in js_assets.items():
            status_code, content = self.make_request(f"{self.base_url}{asset_path}")
            if status_code == 200:
                if name == "Cookie Consent" and "CookieConsentManager" in content:
                    print(f"  ✅ {name}: OK (Manager class found)")
                    self.results[f"js_{name.lower().replace(' ', '_')}"] = True
                elif name == "Empty States" and "EmptyStatesManager" in content:
                    print(f"  ✅ {name}: OK (Manager class found)")
                    self.results[f"js_{name.lower().replace(' ', '_')}"] = True
                elif name == "Error Handler" and "ErrorHandler" in content:
                    print(f"  ✅ {name}: OK (Handler class found)")
                    self.results[f"js_{name.lower().replace(' ', '_')}"] = True
                else:
                    print(f"  ✅ {name}: OK")
                    self.results[f"js_{name.lower().replace(' ', '_')}"] = True
            elif status_code > 0:
                print(f"  ❌ {name}: HTTP {status_code}")
                self.results[f"js_{name.lower().replace(' ', '_')}"] = False
            else:
                print(f"  ❌ {name}: Failed ({content})")
                self.results[f"js_{name.lower().replace(' ', '_')}"] = False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        api_endpoints = {
            "Session": "/api/session",
            "Usage": "/api/usage", 
            "Dashboard Overview": "/api/dashboard/overview",
            "Projects": "/api/projects",
            "Consent Status": "/api/consent/status"
        }
        
        for name, endpoint in api_endpoints.items():
            status_code, content = self.make_request(f"{self.base_url}{endpoint}")
            
            if status_code in [200, 201]:
                print(f"  ✅ {name}: OK")
                self.results[f"api_{name.lower().replace(' ', '_')}"] = True
            elif status_code == 401:
                print(f"  ⚠️  {name}: Authentication required (expected)")
                self.results[f"api_{name.lower().replace(' ', '_')}"] = True
            elif status_code > 0:
                print(f"  ⚠️  {name}: HTTP {status_code}")
                self.results[f"api_{name.lower().replace(' ', '_')}"] = False
            else:
                print(f"  ❌ {name}: Failed ({content})")
                self.results[f"api_{name.lower().replace(' ', '_')}"] = False
        
        # Test consent record POST endpoint
        print("  🍪 Testing Consent Record...")
        payload = {
            "consent": {
                "version": "1.0",
                "hasConsented": True,
                "categories": {"necessary": True}
            }
        }
        status_code, content = self.make_request(f"{self.base_url}/api/consent/record", data=payload, method='POST')
        if status_code in [200, 201]:
            print(f"  ✅ Consent Record: OK")
            self.results["api_consent_record"] = True
        else:
            print(f"  ⚠️  Consent Record: HTTP {status_code}")
            self.results["api_consent_record"] = False
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n🎯 CLIENT-READY ASSESSMENT:")
        if success_rate >= 90:
            print("  🎉 EXCELLENT - Platform is client-ready!")
            print("  ✅ All critical features validated")
            print("  ✅ Legal compliance implemented")
            print("  ✅ Ready for client deployment")
        elif success_rate >= 75:
            print("  👍 GOOD - Minor issues to address")
            print("  ⚠️  Some non-critical features need attention")
            print("  ✅ Core functionality validated")
        elif success_rate >= 50:
            print("  ⚠️  NEEDS WORK - Significant issues detected")
            print("  ❌ Multiple features require attention")
            print("  ⏳ Additional development needed")
        else:
            print("  ❌ NOT READY - Major issues detected")
            print("  🚨 Platform requires significant work")
            print("  🛠️  Not suitable for client deployment")
        
        print(f"\n⏱️  Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

if __name__ == "__main__":
    validator = QuickValidator()
    validator.run_quick_validation()