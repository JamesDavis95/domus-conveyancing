"""
Phase 2B: Council System Integration
===================================

Integrations with council back-office systems:
- Civica
- Capita 
- Northgate
- Academy
"""
import httpx
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

@dataclass
class CouncilConfig:
    """Configuration for council system integration"""
    council_code: str
    system_type: str  # civica, capita, northgate, academy
    api_endpoint: str
    auth_token: str
    webhook_url: Optional[str] = None

class CouncilIntegrationEngine:
    """Handles integrations with various council systems"""
    
    def __init__(self):
        self.integrations = {
            "civica": CivicaIntegration(),
            "capita": CapitaIntegration(),
            "northgate": NorthgateIntegration(),
            "academy": AcademyIntegration()
        }
    
    async def sync_matter_to_council(self, matter: "LAMatter", config: CouncilConfig) -> Dict[str, Any]:
        """Sync LA matter to council back-office system"""
        integration = self.integrations.get(config.system_type)
        if not integration:
            raise HTTPException(400, f"Unsupported council system: {config.system_type}")
            
        return await integration.create_matter(matter, config)
    
    async def receive_council_update(self, webhook_data: Dict[str, Any], config: CouncilConfig) -> Dict[str, Any]:
        """Handle updates from council systems"""
        integration = self.integrations.get(config.system_type)
        return await integration.process_webhook(webhook_data, config)

class CivicaIntegration:
    """Civica system integration"""
    
    async def create_matter(self, matter: "LAMatter", config: CouncilConfig) -> Dict[str, Any]:
        """Create matter in Civica system"""
        payload = {
            "reference": matter.ref,
            "applicant": {
                "name": matter.applicant_name,
                "email": matter.applicant_email,
                "phone": matter.applicant_phone
            },
            "property": {
                "address": matter.address,
                "uprn": matter.uprn
            },
            "searches_requested": {
                "llc1": matter.llc1_requested == "true",
                "con29": matter.con29_requested == "true"
            },
            "priority": matter.priority,
            "sla_due_date": matter.sla_due_date.isoformat() if matter.sla_due_date else None
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_endpoint}/matters",
                json=payload,
                headers={"Authorization": f"Bearer {config.auth_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def process_webhook(self, data: Dict[str, Any], config: CouncilConfig) -> Dict[str, Any]:
        """Process Civica webhook"""
        # Handle status updates from Civica
        return {"status": "processed", "source": "civica"}

class CapitaIntegration:
    """Capita system integration"""
    
    async def create_matter(self, matter: "LAMatter", config: CouncilConfig) -> Dict[str, Any]:
        """Create matter in Capita system"""
        # Capita-specific API format
        payload = {
            "caseReference": matter.ref,
            "customerDetails": {
                "fullName": matter.applicant_name,
                "emailAddress": matter.applicant_email,
                "telephoneNumber": matter.applicant_phone
            },
            "propertyDetails": {
                "fullAddress": matter.address,
                "uprn": matter.uprn
            },
            "serviceRequest": {
                "llc1Search": matter.llc1_requested == "true",
                "con29Search": matter.con29_requested == "true",
                "priority": matter.priority.upper()
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_endpoint}/api/v1/local-land-charges",
                json=payload,
                headers={
                    "X-API-Key": config.auth_token,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def process_webhook(self, data: Dict[str, Any], config: CouncilConfig) -> Dict[str, Any]:
        """Process Capita webhook"""
        return {"status": "processed", "source": "capita"}

class NorthgateIntegration:
    """Northgate system integration"""
    
    async def create_matter(self, matter: "LAMatter", config: CouncilConfig) -> Dict[str, Any]:
        """Create matter in Northgate system"""
        # Northgate M3/Planning Portal integration
        payload = {
            "ApplicationReference": matter.ref,
            "ApplicantName": matter.applicant_name,
            "ApplicantEmail": matter.applicant_email,
            "PropertyAddress": matter.address,
            "UPRN": matter.uprn,
            "SearchTypes": [],
            "Priority": matter.priority,
            "DueDate": matter.sla_due_date.isoformat() if matter.sla_due_date else None
        }
        
        if matter.llc1_requested == "true":
            payload["SearchTypes"].append("LLC1")
        if matter.con29_requested == "true":
            payload["SearchTypes"].append("CON29")
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_endpoint}/LocalLandCharges/CreateApplication",
                json=payload,
                headers={"Authorization": f"Bearer {config.auth_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def process_webhook(self, data: Dict[str, Any], config: CouncilConfig) -> Dict[str, Any]:
        """Process Northgate webhook"""
        return {"status": "processed", "source": "northgate"}

class AcademyIntegration:
    """Academy system integration"""
    
    async def create_matter(self, matter: "LAMatter", config: CouncilConfig) -> Dict[str, Any]:
        """Create matter in Academy system"""
        # Academy-specific format
        payload = {
            "reference": matter.ref,
            "customer": {
                "name": matter.applicant_name,
                "email": matter.applicant_email,
                "telephone": matter.applicant_phone,
                "address": matter.applicant_address
            },
            "subject_property": {
                "address": matter.address,
                "uprn": matter.uprn
            },
            "search_products": {
                "local_land_charges": matter.llc1_requested == "true",
                "con29_enquiries": matter.con29_requested == "true"
            },
            "service_level": matter.priority,
            "target_completion": matter.sla_due_date.isoformat() if matter.sla_due_date else None
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.api_endpoint}/search-applications",
                json=payload,
                headers={
                    "X-API-Key": config.auth_token,
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def process_webhook(self, data: Dict[str, Any], config: CouncilConfig) -> Dict[str, Any]:
        """Process Academy webhook"""
        return {"status": "processed", "source": "academy"}

# Router for council integrations
router = APIRouter(prefix="/integrations", tags=["Council Systems"])

@router.post("/sync-matter/{matter_id}")
async def sync_matter_to_council(
    matter_id: str,
    council_system: str,
    config: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Sync matter to council back-office system"""
    from la.models import LAMatter
    
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(404, "Matter not found")
    
    council_config = CouncilConfig(
        council_code=config.get("council_code", ""),
        system_type=council_system,
        api_endpoint=config.get("api_endpoint", ""),
        auth_token=config.get("auth_token", "")
    )
    
    engine = CouncilIntegrationEngine()
    result = await engine.sync_matter_to_council(matter, council_config)
    
    return {"status": "synced", "result": result}

@router.post("/webhook/{council_system}")
async def receive_council_webhook(
    council_system: str,
    webhook_data: Dict[str, Any]
):
    """Receive updates from council systems"""
    engine = CouncilIntegrationEngine()
    
    # Process webhook based on system type
    config = CouncilConfig(
        council_code=webhook_data.get("council_code", ""),
        system_type=council_system,
        api_endpoint="",
        auth_token=""
    )
    
    result = await engine.receive_council_update(webhook_data, config)
    return result