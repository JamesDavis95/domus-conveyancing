"""
AI Citation Engine
Enforces citations, precedents, and versioning in all AI responses
Blocks suggestions without proper citations and maintains explainability
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import hashlib
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class CitationType(Enum):
    PLANNING_GUIDANCE = "planning_guidance"
    CASE_LAW = "case_law"
    STATUTORY_PROVISION = "statutory_provision"
    LOCAL_PLAN_POLICY = "local_plan_policy"
    HDT_DATA = "hdt_data"
    FIVE_YHLS_DATA = "5yhls_data"
    APPEAL_DECISION = "appeal_decision"
    INSPECTOR_REPORT = "inspector_report"
    GOVERNMENT_CIRCULAR = "government_circular"
    WHITE_PAPER = "white_paper"
    CONSULTATION_RESPONSE = "consultation_response"

class CitationQuality(Enum):
    PRIMARY = "primary"      # Direct statutory/case law
    SECONDARY = "secondary"  # Government guidance
    TERTIARY = "tertiary"    # Local policies/data

@dataclass
class Citation:
    """Individual citation with full provenance"""
    id: str
    type: CitationType
    quality: CitationQuality
    title: str
    authority: str  # LPA, Court, Government Department
    date: datetime
    url: Optional[str]
    section_reference: Optional[str]
    page_numbers: Optional[str]
    paragraph_reference: Optional[str]
    relevance_score: float  # 0.0 - 1.0
    content_excerpt: str
    context: str  # How this citation supports the AI response
    lpa_code: Optional[str]  # For LPA-specific citations
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class ModelVersion:
    """AI model version information"""
    model_name: str
    version: str
    provider: str
    training_cutoff: datetime
    capabilities: List[str]
    temperature: float
    max_tokens: int
    
@dataclass
class AIResponse:
    """Comprehensive AI response with explainability"""
    response_id: str
    query: str
    response_text: str
    model_version: ModelVersion
    citations: List[Citation]
    confidence_score: float
    reasoning_chain: List[str]  # Step-by-step reasoning
    assumptions: List[str]
    limitations: List[str]
    alternative_interpretations: List[str]
    created_at: datetime
    lpa_context: Optional[Dict[str, Any]] = None
    analysis_snapshot: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.response_id:
            self.response_id = str(uuid.uuid4())

class CitationEngine:
    """Core engine for AI citation enforcement and explainability"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.knowledge_base_path = knowledge_base_path or "data/knowledge_base"
        self.min_citations_required = 2
        self.min_confidence_threshold = 0.7
        self.citation_index = {}
        self.load_citation_index()
    
    def load_citation_index(self):
        """Load prebuilt citation index from knowledge base"""
        try:
            index_path = Path(self.knowledge_base_path) / "citation_index.json"
            if index_path.exists():
                with open(index_path, 'r') as f:
                    self.citation_index = json.load(f)
                logger.info(f"Loaded {len(self.citation_index)} citations from index")
            else:
                logger.warning("Citation index not found, starting with empty index")
                self.citation_index = {}
        except Exception as e:
            logger.error(f"Failed to load citation index: {e}")
            self.citation_index = {}
    
    def validate_ai_response(self, response: AIResponse) -> Dict[str, Any]:
        """Validate AI response meets citation and explainability requirements"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "citation_score": 0.0,
            "explainability_score": 0.0
        }
        
        # Check minimum citations
        if len(response.citations) < self.min_citations_required:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Insufficient citations: {len(response.citations)} provided, "
                f"{self.min_citations_required} required"
            )
        
        # Check citation quality
        primary_citations = [c for c in response.citations if c.quality == CitationQuality.PRIMARY]
        if not primary_citations:
            validation_result["warnings"].append("No primary sources cited")
        
        # Check confidence threshold
        if response.confidence_score < self.min_confidence_threshold:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Confidence too low: {response.confidence_score:.2f}, "
                f"minimum {self.min_confidence_threshold} required"
            )
        
        # Check citation relevance
        low_relevance_citations = [c for c in response.citations if c.relevance_score < 0.5]
        if low_relevance_citations:
            validation_result["warnings"].append(
                f"{len(low_relevance_citations)} citations have low relevance scores"
            )
        
        # Check explainability completeness
        if not response.reasoning_chain:
            validation_result["errors"].append("No reasoning chain provided")
            validation_result["valid"] = False
        
        if not response.assumptions:
            validation_result["warnings"].append("No assumptions documented")
        
        if not response.limitations:
            validation_result["warnings"].append("No limitations documented")
        
        # Calculate scores
        validation_result["citation_score"] = self._calculate_citation_score(response.citations)
        validation_result["explainability_score"] = self._calculate_explainability_score(response)
        
        return validation_result
    
    def _calculate_citation_score(self, citations: List[Citation]) -> float:
        """Calculate overall citation quality score"""
        if not citations:
            return 0.0
        
        # Weight by citation quality and relevance
        quality_weights = {
            CitationQuality.PRIMARY: 1.0,
            CitationQuality.SECONDARY: 0.7,
            CitationQuality.TERTIARY: 0.4
        }
        
        total_score = 0.0
        for citation in citations:
            quality_weight = quality_weights[citation.quality]
            relevance_weight = citation.relevance_score
            total_score += quality_weight * relevance_weight
        
        return min(total_score / len(citations), 1.0)
    
    def _calculate_explainability_score(self, response: AIResponse) -> float:
        """Calculate explainability completeness score"""
        score = 0.0
        max_score = 6.0
        
        # Reasoning chain (2 points)
        if response.reasoning_chain:
            score += 2.0
        
        # Assumptions documented (1 point)
        if response.assumptions:
            score += 1.0
        
        # Limitations documented (1 point)
        if response.limitations:
            score += 1.0
        
        # Alternative interpretations (1 point)
        if response.alternative_interpretations:
            score += 1.0
        
        # Confidence score provided (1 point)
        if response.confidence_score > 0:
            score += 1.0
        
        return score / max_score
    
    def find_citations(self, query: str, lpa_code: str = None, limit: int = 10) -> List[Citation]:
        """Find relevant citations for a query"""
        # This would integrate with vector search/semantic matching
        # For now, return mock citations for demonstration
        
        citations = []
        
        # Mock planning guidance citation
        citations.append(Citation(
            id=str(uuid.uuid4()),
            type=CitationType.PLANNING_GUIDANCE,
            quality=CitationQuality.SECONDARY,
            title="National Planning Policy Framework",
            authority="Department for Levelling Up, Housing and Communities",
            date=datetime(2023, 12, 19),
            url="https://www.gov.uk/government/publications/national-planning-policy-framework--2",
            section_reference="Section 11: Making effective use of land",
            page_numbers="45-52",
            paragraph_reference="Para 124-132",
            relevance_score=0.85,
            content_excerpt="Planning policies and decisions should support development that makes efficient use of land...",
            context="Provides national policy context for land use efficiency requirements",
            lpa_code=lpa_code
        ))
        
        # Mock case law citation if relevant
        if "appeal" in query.lower() or "refusal" in query.lower():
            citations.append(Citation(
                id=str(uuid.uuid4()),
                type=CitationType.CASE_LAW,
                quality=CitationQuality.PRIMARY,
                title="R (Samuel Smith Old Brewery) v North Yorkshire CC",
                authority="Court of Appeal",
                date=datetime(2020, 7, 21),
                url="https://www.bailii.org/ew/cases/EWCA/Civ/2020/989.html",
                section_reference="[2020] EWCA Civ 989",
                page_numbers="1-15",
                paragraph_reference="Para 45-52",
                relevance_score=0.78,
                content_excerpt="The court held that the planning authority must give clear reasons for refusal...",
                context="Establishes precedent for reasoning requirements in planning decisions",
                lpa_code=lpa_code
            ))
        
        return citations[:limit]
    
    def enhance_with_lpa_context(self, response: AIResponse, lpa_code: str) -> AIResponse:
        """Enhance response with LPA-specific context including HDT and 5YHLS data"""
        try:
            # Mock LPA context - would integrate with actual data sources
            lpa_context = {
                "lpa_code": lpa_code,
                "lpa_name": f"Local Planning Authority {lpa_code}",
                "hdt_data": {
                    "housing_delivery_test_score": 95,
                    "test_year": "2023",
                    "status": "pass",
                    "action_plan_required": False,
                    "presumption_applies": False
                },
                "five_yhls_data": {
                    "five_year_supply": 5.2,
                    "assessment_date": "2024-04-01",
                    "buffer_applied": "20%",
                    "deliverable_sites": 1250,
                    "requirement_per_year": 240
                },
                "local_plan_status": {
                    "adoption_date": "2019-03-15",
                    "review_date": "2024-03-15",
                    "policies_map_updated": "2023-09-01"
                },
                "recent_appeals": {
                    "total_appeals_2023": 45,
                    "allowed_rate": 0.33,
                    "common_reasons_for_dismissal": [
                        "Highway safety concerns",
                        "Impact on character and appearance",
                        "Inadequate housing land supply evidence"
                    ]
                }
            }
            
            response.lpa_context = lpa_context
            
            # Add LPA-specific citations
            lpa_citations = self._get_lpa_specific_citations(lpa_code)
            response.citations.extend(lpa_citations)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to enhance with LPA context: {e}")
            return response
    
    def _get_lpa_specific_citations(self, lpa_code: str) -> List[Citation]:
        """Get LPA-specific citations including HDT and 5YHLS data"""
        citations = []
        
        # HDT data citation
        citations.append(Citation(
            id=str(uuid.uuid4()),
            type=CitationType.HDT_DATA,
            quality=CitationQuality.SECONDARY,
            title="Housing Delivery Test Results",
            authority="Ministry of Housing, Communities & Local Government",
            date=datetime(2024, 1, 15),
            url=f"https://www.gov.uk/government/publications/housing-delivery-test-2023-measurement",
            section_reference=f"LPA: {lpa_code}",
            page_numbers="1-5",
            paragraph_reference=None,
            relevance_score=0.90,
            content_excerpt="Housing Delivery Test score: 95% (Pass)",
            context="Current HDT performance affects planning policy application",
            lpa_code=lpa_code
        ))
        
        # 5YHLS data citation
        citations.append(Citation(
            id=str(uuid.uuid4()),
            type=CitationType.FIVE_YHLS_DATA,
            quality=CitationQuality.SECONDARY,
            title="Five Year Housing Land Supply Assessment",
            authority=f"Local Planning Authority {lpa_code}",
            date=datetime(2024, 4, 1),
            url=None,
            section_reference="Annual Monitoring Report 2024",
            page_numbers="12-18",
            paragraph_reference=None,
            relevance_score=0.88,
            content_excerpt="5.2 years of deliverable housing supply identified",
            context="Current housing land supply position affects presumption in favour",
            lpa_code=lpa_code
        ))
        
        return citations
    
    def create_analysis_snapshot(self, response: AIResponse) -> Dict[str, Any]:
        """Create comprehensive analysis snapshot for audit trail"""
        snapshot = {
            "snapshot_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "response_summary": {
                "response_id": response.response_id,
                "query_hash": hashlib.sha256(response.query.encode()).hexdigest(),
                "response_length": len(response.response_text),
                "citation_count": len(response.citations),
                "confidence_score": response.confidence_score
            },
            "model_information": asdict(response.model_version),
            "citation_analysis": {
                "primary_sources": len([c for c in response.citations if c.quality == CitationQuality.PRIMARY]),
                "secondary_sources": len([c for c in response.citations if c.quality == CitationQuality.SECONDARY]),
                "tertiary_sources": len([c for c in response.citations if c.quality == CitationQuality.TERTIARY]),
                "average_relevance": sum(c.relevance_score for c in response.citations) / len(response.citations) if response.citations else 0,
                "citation_types": list(set(c.type.value for c in response.citations))
            },
            "explainability_metrics": {
                "reasoning_steps": len(response.reasoning_chain),
                "assumptions_count": len(response.assumptions),
                "limitations_count": len(response.limitations),
                "alternative_interpretations": len(response.alternative_interpretations)
            },
            "lpa_context_summary": response.lpa_context if response.lpa_context else None,
            "validation_result": self.validate_ai_response(response)
        }
        
        response.analysis_snapshot = snapshot
        return snapshot
    
    def block_uncited_suggestion(self, response_text: str, citations: List[Citation]) -> bool:
        """Determine if a suggestion should be blocked for insufficient citations"""
        # Check for suggestion keywords
        suggestion_keywords = [
            "recommend", "suggest", "should", "would advise", "propose",
            "best to", "consider", "ought to", "preferable", "advisable"
        ]
        
        contains_suggestion = any(keyword in response_text.lower() for keyword in suggestion_keywords)
        
        if contains_suggestion:
            # Require at least one primary or secondary citation for suggestions
            quality_citations = [c for c in citations if c.quality in [CitationQuality.PRIMARY, CitationQuality.SECONDARY]]
            
            if not quality_citations:
                logger.warning("Blocking suggestion due to insufficient quality citations")
                return True
        
        return False
    
    def format_citation_display(self, citation: Citation) -> str:
        """Format citation for display in AI responses"""
        citation_parts = []
        
        # Authority and title
        citation_parts.append(f"{citation.authority}")
        citation_parts.append(f"'{citation.title}'")
        
        # Date
        citation_parts.append(f"({citation.date.strftime('%Y')})")
        
        # Reference details
        if citation.section_reference:
            citation_parts.append(f"{citation.section_reference}")
        
        if citation.paragraph_reference:
            citation_parts.append(f"{citation.paragraph_reference}")
        
        # URL if available
        if citation.url:
            citation_parts.append(f"Available at: {citation.url}")
        
        return " ".join(citation_parts)
    
    def export_explainability_report(self, response: AIResponse) -> Dict[str, Any]:
        """Export comprehensive explainability report"""
        return {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "response_details": {
                "response_id": response.response_id,
                "query": response.query,
                "response_text": response.response_text,
                "created_at": response.created_at.isoformat()
            },
            "model_transparency": asdict(response.model_version),
            "citation_provenance": [asdict(c) for c in response.citations],
            "reasoning_transparency": {
                "reasoning_chain": response.reasoning_chain,
                "assumptions": response.assumptions,
                "limitations": response.limitations,
                "alternative_interpretations": response.alternative_interpretations,
                "confidence_score": response.confidence_score
            },
            "lpa_context": response.lpa_context,
            "validation_summary": self.validate_ai_response(response),
            "analysis_snapshot": response.analysis_snapshot
        }