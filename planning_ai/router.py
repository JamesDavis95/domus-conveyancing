"""
Planning AI API Router
FastAPI endpoints for AI-powered planning analysis
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, BackgroundTasks
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid
import tempfile
import os

from .schemas import (
    SiteInput, 
    Constraint, 
    Score, 
    Recommendation,
    DocArtifact,
    PlanningAnalysis,
    PropertyData
)
from .scoring import calculate_approval_probability
from .constraints import detect_planning_constraints  
from .recommender import generate_recommendations
from .extractors import extract_document_content


router = APIRouter(prefix="/planning-ai", tags=["Planning AI"])


@router.post("/analyze", response_model=PlanningAnalysis)
async def analyze_planning_application(site_input: SiteInput) -> PlanningAnalysis:
    """
    Comprehensive AI analysis of planning application
    
    Performs:
    - Constraint detection and assessment
    - Approval probability scoring
    - Improvement recommendations
    - Policy compliance checking
    """
    
    try:
        # Run AI analysis components in parallel
        constraints_task = detect_planning_constraints(site_input)
        scoring_task = calculate_approval_probability(site_input)
        
        constraints, score_result = await asyncio.gather(
            constraints_task, 
            scoring_task
        )
        
        # Generate recommendations based on constraints and scoring
        recommendations = await generate_recommendations(
            site_input, 
            constraints, 
            score_result
        )
        
        return PlanningAnalysis(
            site_input=site_input,
            constraints=constraints,
            score=score_result,
            recommendations=recommendations,
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            processing_time_ms=0  # Would track actual processing time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/constraints")
async def detect_constraints(site_input: SiteInput) -> List[Constraint]:
    """Detect planning constraints for a site"""
    
    try:
        constraints = await detect_planning_constraints(site_input)
        return constraints
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Constraint detection failed: {str(e)}"
        )


@router.post("/score") 
async def score_application(site_input: SiteInput) -> Score:
    """Calculate approval probability score for planning application"""
    
    try:
        score = await calculate_approval_probability(site_input)
        return score
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}"
        )


@router.post("/recommendations")
async def get_recommendations(
    site_input: SiteInput,
    constraints: Optional[List[Constraint]] = None,
    score: Optional[Score] = None
) -> List[Recommendation]:
    """Generate improvement recommendations"""
    
    try:
        # If constraints/score not provided, calculate them
        if constraints is None:
            constraints = await detect_planning_constraints(site_input)
        
        if score is None:
            score = await calculate_approval_probability(site_input)
        
        recommendations = await generate_recommendations(
            site_input, 
            constraints, 
            score
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}"
        )


@router.post("/extract-document")
async def extract_planning_document(
    file: UploadFile = File(...),
    document_type: str = "generic"
) -> Dict[str, Any]:
    """
    Extract and structure content from planning documents
    
    Supports:
    - Local Plans
    - Supplementary Planning Documents (SPDs) 
    - Appeal Decisions
    - Officer Reports
    - Generic planning documents
    """
    
    # Validate file type
    allowed_types = ['application/pdf', 'application/msword', 
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/html', 'text/plain']
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Validate document type
    valid_doc_types = ['local_plan', 'spd', 'appeal_decision', 'officer_report', 'generic']
    if document_type not in valid_doc_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Must be one of: {', '.join(valid_doc_types)}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract structured content
            extracted_content = await extract_document_content(
                temp_file_path, 
                document_type
            )
            
            return {
                'filename': file.filename,
                'document_type': document_type,
                'file_size': len(content),
                'extraction_id': str(uuid.uuid4()),
                'extracted_content': extracted_content,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document extraction failed: {str(e)}"
        )


@router.get("/property/{property_id}")
async def get_property_data(property_id: str) -> PropertyData:
    """
    Get comprehensive property data from multiple sources
    
    Integrates:
    - Land Registry data
    - EPC ratings
    - Flood risk data  
    - Planning history
    - Conservation area status
    """
    
    try:
        # Placeholder for property data integration
        # In production, would integrate with actual APIs
        
        property_data = PropertyData(
            property_id=property_id,
            address="123 Example Street, Example Town, EX1 2MP",
            coordinates=(51.5074, -0.1278),
            land_registry={
                'title_number': 'EX123456',
                'tenure': 'Freehold',
                'proprietor': 'Example Owner',
                'registered_date': '2020-01-15'
            },
            epc_data={
                'rating': 'C',
                'score': 72,
                'potential_rating': 'B',
                'potential_score': 84,
                'valid_until': '2030-01-15'
            },
            flood_risk={
                'river_sea': 'Very Low',
                'surface_water': 'Low', 
                'groundwater': 'Very Low',
                'reservoir': 'Very Low'
            },
            planning_history=[
                {
                    'reference': '22/001234/FUL',
                    'description': 'Single storey rear extension',
                    'decision': 'Approved',
                    'decision_date': '2022-06-15'
                }
            ],
            constraints={
                'conservation_area': False,
                'listed_building': False,
                'article_4_direction': False,
                'tree_preservation_orders': [],
                'other_designations': []
            }
        )
        
        return property_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Property data retrieval failed: {str(e)}"
        )


@router.get("/nearby-decisions/{postcode}")
async def get_nearby_decisions(
    postcode: str,
    radius_km: float = 1.0,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Get recent planning decisions near a location
    
    Useful for understanding local decision patterns and precedents
    """
    
    try:
        # Placeholder for nearby decisions lookup
        # In production, would query planning applications database
        
        decisions = [
            {
                'reference': '23/001234/FUL',
                'address': '10 Nearby Street',
                'description': 'Two storey side extension',
                'decision': 'Approved',
                'decision_date': '2023-08-15',
                'distance_m': 150,
                'officer_comments': 'Acceptable impact on character'
            },
            {
                'reference': '23/001567/HOU', 
                'address': '25 Adjacent Road',
                'description': 'Loft conversion with dormer',
                'decision': 'Refused',
                'decision_date': '2023-09-02', 
                'distance_m': 280,
                'officer_comments': 'Unacceptable impact on streetscene'
            }
        ]
        
        return {
            'postcode': postcode,
            'radius_km': radius_km,
            'total_decisions': len(decisions),
            'decisions': decisions[:limit],
            'summary': {
                'approved': 1,
                'refused': 1,
                'approval_rate': 50.0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Nearby decisions lookup failed: {str(e)}"
        )


@router.get("/policy-search")
async def search_planning_policies(
    query: str,
    document_types: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search planning policies and guidance
    
    Searches across:
    - Local Plan policies
    - Supplementary Planning Documents
    - National Planning Policy Framework
    - Planning Practice Guidance
    """
    
    try:
        # Placeholder for policy search
        # In production, would use vector search across policy database
        
        results = [
            {
                'policy_id': 'H1',
                'title': 'Housing Development',
                'document': 'Local Plan 2021-2038',
                'content_preview': 'Housing development will be supported where...',
                'relevance_score': 0.95
            },
            {
                'policy_id': 'D2',
                'title': 'Design Quality',  
                'document': 'Design Guide SPD',
                'content_preview': 'All development must achieve high quality design...',
                'relevance_score': 0.87
            }
        ]
        
        return {
            'query': query,
            'total_results': len(results),
            'results': results[:limit],
            'document_types_searched': document_types or ['all']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Policy search failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for planning AI services"""
    
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'constraints_detection': 'operational',
            'approval_scoring': 'operational', 
            'recommendations': 'operational',
            'document_extraction': 'operational'
        },
        'version': '1.0.0'
    }