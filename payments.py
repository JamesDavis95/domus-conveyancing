"""
Payment Integration Module for LA System
Supports Gov.UK Pay and manual payment processing
"""
import json
import logging
import requests
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os

logger = logging.getLogger(__name__)

class PaymentEngine:
    """Handles payment processing for LA matters"""
    
    def __init__(self):
        self.govuk_pay_api_key = os.getenv("GOVUK_PAY_API_KEY", "test_key")
        self.govuk_pay_base_url = os.getenv("GOVUK_PAY_URL", "https://publicapi.payments.service.gov.uk")
        
        # Fee structure (configurable)
        self.fee_structure = {
            "llc1": {"standard": 15.00, "personal": 15.00, "commercial": 15.00},
            "con29": {"residential": 92.00, "commercial": 434.00},
            "con29o": {"optional": 18.00},
            "additional_enquiry": {"per_question": 18.00}
        }
        
    async def calculate_fees(self, matter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total fees for a matter"""
        try:
            total = Decimal('0.00')
            breakdown = {}
            
            # LLC1 fee
            if matter_data.get("llc1_requested") == "true":
                llc1_fee = Decimal(str(self.fee_structure["llc1"]["standard"]))
                breakdown["llc1"] = float(llc1_fee)
                total += llc1_fee
            
            # CON29 fee (depends on property type)
            if matter_data.get("con29_requested") == "true":
                property_type = matter_data.get("property_type", "residential")
                con29_fee = Decimal(str(self.fee_structure["con29"].get(property_type, 92.00)))
                breakdown["con29"] = float(con29_fee)
                total += con29_fee
            
            # CON29O fee
            if matter_data.get("con29o_requested") == "true":
                con29o_fee = Decimal(str(self.fee_structure["con29o"]["optional"]))
                breakdown["con29o"] = float(con29o_fee)
                total += con29o_fee
            
            # Additional enquiries
            additional = matter_data.get("additional_enquiries", [])
            if additional:
                if isinstance(additional, str):
                    additional = json.loads(additional)
                enquiry_count = len(additional)
                enquiry_fee = Decimal(str(self.fee_structure["additional_enquiry"]["per_question"])) * enquiry_count
                breakdown["additional_enquiries"] = {"count": enquiry_count, "fee": float(enquiry_fee)}
                total += enquiry_fee
            
            return {
                "total": float(total),
                "currency": "GBP", 
                "breakdown": breakdown,
                "vat_included": True
            }
            
        except Exception as e:
            logger.error(f"Fee calculation failed: {e}")
            return {"total": 0.00, "currency": "GBP", "breakdown": {}, "error": str(e)}
    
    async def create_govuk_payment(self, matter_id: str, amount: float, description: str, return_url: str) -> Dict[str, Any]:
        """Create Gov.UK Pay payment"""
        try:
            headers = {
                "Authorization": f"Bearer {self.govuk_pay_api_key}",
                "Content-Type": "application/json"
            }
            
            payment_data = {
                "amount": int(amount * 100),  # Convert to pence
                "reference": f"LA-{matter_id}",
                "description": description,
                "return_url": return_url,
                "language": "en"
            }
            
            response = requests.post(
                f"{self.govuk_pay_base_url}/v1/payments",
                headers=headers,
                json=payment_data,
                timeout=30
            )
            
            if response.status_code == 201:
                payment_response = response.json()
                return {
                    "success": True,
                    "payment_id": payment_response["payment_id"],
                    "payment_url": payment_response["_links"]["next_url"]["href"],
                    "status": payment_response["state"]["status"],
                    "amount": amount,
                    "reference": payment_response["reference"]
                }
            else:
                logger.error(f"Gov.UK Pay error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Payment creation failed: {response.text}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            logger.error(f"Gov.UK Pay request failed: {e}")
            return {
                "success": False,
                "error": f"Payment system error: {str(e)}"
            }
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check Gov.UK Pay payment status"""
        try:
            headers = {
                "Authorization": f"Bearer {self.govuk_pay_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.govuk_pay_base_url}/v1/payments/{payment_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                return {
                    "success": True,
                    "status": payment_data["state"]["status"],
                    "finished": payment_data["state"]["finished"],
                    "amount": payment_data["amount"] / 100,  # Convert from pence
                    "reference": payment_data["reference"],
                    "created_date": payment_data["created_date"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Status check failed: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Payment status check failed: {e}")
            return {
                "success": False,
                "error": f"Status check error: {str(e)}"
            }
    
    async def process_manual_payment(self, matter_id: str, amount: float, method: str, reference: str) -> Dict[str, Any]:
        """Process manual payment (BACS, cheque, etc.)"""
        try:
            return {
                "success": True,
                "payment_id": f"MANUAL-{matter_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "success",
                "method": method,
                "reference": reference,
                "amount": amount,
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Manual payment processing failed: {e}")
            return {
                "success": False,
                "error": f"Manual payment error: {str(e)}"
            }
    
    async def check_exemptions(self, matter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if matter qualifies for fee exemption"""
        exemptions = []
        
        # Check various exemption criteria
        if matter_data.get("applicant_type") == "charity":
            exemptions.append("charity_exemption")
        
        if matter_data.get("property_value", 0) < 40000:  # Example threshold
            exemptions.append("low_value_property")
        
        if matter_data.get("legal_aid") == "true":
            exemptions.append("legal_aid")
        
        return {
            "has_exemptions": len(exemptions) > 0,
            "exemptions": exemptions,
            "total_exemption": len(exemptions) > 0  # All or nothing for simplicity
        }

# Global payment engine instance
payment_engine = PaymentEngine()