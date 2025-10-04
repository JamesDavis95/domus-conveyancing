"""
Compliance Module for Domus Conveyancing Platform
Comprehensive compliance documentation and policies
"""

from .privacy_policy import get_privacy_policy
from .terms_of_service import get_terms_of_service
from .cookie_policy import get_cookie_policy
from .data_retention_schedule import get_data_retention_schedule
from .gdpr_compliance import get_gdpr_compliance_guide

__all__ = [
    'get_privacy_policy',
    'get_terms_of_service', 
    'get_cookie_policy',
    'get_data_retention_schedule',
    'get_gdpr_compliance_guide'
]

class ComplianceDocumentManager:
    """Manages all compliance documentation"""
    
    def __init__(self):
        self.documents = {
            'privacy_policy': get_privacy_policy,
            'terms_of_service': get_terms_of_service,
            'cookie_policy': get_cookie_policy,
            'data_retention_schedule': get_data_retention_schedule,
            'gdpr_compliance': get_gdpr_compliance_guide
        }
    
    def get_document(self, document_type: str, **kwargs) -> str:
        """Get a specific compliance document"""
        
        if document_type not in self.documents:
            raise ValueError(f"Unknown document type: {document_type}")
        
        return self.documents[document_type](**kwargs)
    
    def get_all_documents(self) -> dict:
        """Get all compliance documents"""
        
        return {
            doc_type: func()
            for doc_type, func in self.documents.items()
        }
    
    def get_document_summary(self) -> dict:
        """Get summary of all compliance documents"""
        
        return {
            'privacy_policy': {
                'title': 'Privacy Policy',
                'description': 'GDPR-compliant privacy policy explaining data collection, use, and protection',
                'last_updated': 'October 2025',
                'compliance': ['UK GDPR', 'Data Protection Act 2018']
            },
            'terms_of_service': {
                'title': 'Terms of Service',
                'description': 'Legal terms and conditions for platform usage and legal services',
                'last_updated': 'October 2025',
                'compliance': ['SRA Regulations', 'UK Contract Law']
            },
            'cookie_policy': {
                'title': 'Cookie Policy',
                'description': 'Comprehensive cookie usage and management policy',
                'last_updated': 'October 2025',
                'compliance': ['PECR', 'UK GDPR', 'Cookie Regulations']
            },
            'data_retention_schedule': {
                'title': 'Data Retention Schedule',
                'description': 'Detailed data retention periods and disposal procedures',
                'last_updated': 'October 2025',
                'compliance': ['SRA Requirements', 'HMRC Regulations', 'AML Regulations']
            },
            'gdpr_compliance': {
                'title': 'GDPR Compliance Framework',
                'description': 'Comprehensive GDPR compliance documentation and procedures',
                'last_updated': 'October 2025',
                'compliance': ['UK GDPR', 'Data Protection Act 2018', 'Professional Standards']
            }
        }

# Global compliance manager instance
compliance_manager = ComplianceDocumentManager()