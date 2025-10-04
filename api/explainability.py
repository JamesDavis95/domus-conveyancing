"""
AI Explainability API Router
Provides endpoints for managing AI explainability, citations, and response validation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from backend_auth import get_current_user
from lib.rbac import require_admin
from models import get_db
from lib.ai_explainability.citation_engine import CitationEngine, Citation, CitationType, CitationQuality
from lib.ai_explainability.response_processor import AIResponseProcessor

router = APIRouter(prefix="/api/explainability", tags=["AI Explainability"])

# Initialize explainability components
citation_engine = CitationEngine()
response_processor = AIResponseProcessor()

# Request/Response Models
class CitationRequest(BaseModel):
    query: str
    lpa_code: Optional[str] = None
    limit: int = 10

class ValidationConfigRequest(BaseModel):
    min_citations_required: Optional[int] = None
    min_confidence_threshold: Optional[float] = None
    require_primary_citations: Optional[bool] = None
    block_uncited_suggestions: Optional[bool] = None

class ExplainabilityReportRequest(BaseModel):
    response_id: str
    include_full_analysis: bool = True

class ResponseAnalysisRequest(BaseModel):
    query: str
    response_text: str
    model_info: Dict[str, Any]
    lpa_code: Optional[str] = None

# Citation Management Endpoints
@router.get("/citations/search")
async def search_citations(
    query: str = Query(..., description="Search query for citations"),
    lpa_code: Optional[str] = Query(None, description="LPA code for local citations"),
    citation_type: Optional[str] = Query(None, description="Filter by citation type"),
    quality: Optional[str] = Query(None, description="Filter by citation quality"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for relevant citations"""
    try:
        citations = citation_engine.find_citations(query, lpa_code, limit)
        
        # Filter by type and quality if specified
        if citation_type:
            citations = [c for c in citations if c.type.value == citation_type]
        
        if quality:
            citations = [c for c in citations if c.quality.value == quality]
        
        return {
            "citations": [
                {
                    "id": c.id,
                    "type": c.type.value,
                    "quality": c.quality.value,
                    "title": c.title,
                    "authority": c.authority,
                    "date": c.date.isoformat(),
                    "url": c.url,
                    "section_reference": c.section_reference,
                    "relevance_score": c.relevance_score,
                    "content_excerpt": c.content_excerpt,
                    "context": c.context,
                    "lpa_code": c.lpa_code
                }
                for c in citations
            ],
            "total_found": len(citations),
            "query": query,
            "lpa_code": lpa_code
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Citation search failed: {str(e)}")

@router.get("/citations/types")
async def get_citation_types(
    current_user = Depends(get_current_user)
):
    """Get available citation types"""
    return {
        "citation_types": [
            {"value": ct.value, "name": ct.value.replace("_", " ").title()}
            for ct in CitationType
        ],
        "citation_qualities": [
            {"value": cq.value, "name": cq.value.title()}
            for cq in CitationQuality
        ]
    }

# Response Validation Endpoints
@router.post("/validate/response")
async def validate_ai_response(
    request: ResponseAnalysisRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate an AI response for explainability compliance"""
    try:
        # Process response through explainability pipeline
        is_valid, processed_response, processing_result = await response_processor.process_ai_response(
            query=request.query,
            raw_response=request.response_text,
            model_info=request.model_info,
            lpa_code=request.lpa_code
        )
        
        # Store validation result in database
        db.execute("""
            INSERT INTO ai_responses 
            (response_id, query, response_text, model_name, model_version, model_provider,
             confidence_score, user_id, lpa_code, is_valid, is_blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            processed_response.response_id,
            request.query,
            request.response_text,
            request.model_info.get('model_name', 'unknown'),
            request.model_info.get('version', '1.0'),
            request.model_info.get('provider', 'unknown'),
            processed_response.confidence_score,
            current_user.get('user_id'),
            request.lpa_code,
            is_valid,
            processing_result.get('blocked', False)
        ))
        
        # Store citations
        for citation in processed_response.citations:
            db.execute("""
                INSERT INTO citations
                (citation_id, response_id, citation_type, citation_quality, title, authority,
                 citation_date, url, section_reference, relevance_score, content_excerpt,
                 context_explanation, lpa_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                citation.id,
                processed_response.response_id,
                citation.type.value,
                citation.quality.value,
                citation.title,
                citation.authority,
                citation.date.date(),
                citation.url,
                citation.section_reference,
                citation.relevance_score,
                citation.content_excerpt,
                citation.context,
                citation.lpa_code
            ))
        
        db.commit()
        
        return {
            "response_id": processed_response.response_id,
            "is_valid": is_valid,
            "validation_result": processing_result["validation"],
            "blocked": processing_result.get("blocked", False),
            "citation_count": len(processed_response.citations),
            "confidence_score": processed_response.confidence_score,
            "explainability_score": processing_result["validation"].get("explainability_score", 0.0),
            "enhanced_response": processed_response.response_text if is_valid else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")

@router.get("/validate/config")
async def get_validation_config(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current validation configuration"""
    try:
        config_result = db.execute("""
            SELECT config_key, config_value FROM explainability_config
        """).fetchall()
        
        config = {row[0]: row[1] for row in config_result}
        
        return {
            "min_citations_required": int(config.get('min_citations_required', 2)),
            "min_confidence_threshold": float(config.get('min_confidence_threshold', 0.7)),
            "require_primary_citations": config.get('require_primary_citations', 'false').lower() == 'true',
            "block_uncited_suggestions": config.get('block_uncited_suggestions', 'true').lower() == 'true',
            "enable_lpa_context": config.get('enable_lpa_context', 'true').lower() == 'true',
            "citation_relevance_threshold": float(config.get('citation_relevance_threshold', 0.5))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get validation config: {str(e)}")

@router.post("/validate/config")
async def update_validation_config(
    request: ValidationConfigRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update validation configuration"""
    try:
        updates = []
        
        if request.min_citations_required is not None:
            updates.append(('min_citations_required', str(request.min_citations_required)))
        
        if request.min_confidence_threshold is not None:
            updates.append(('min_confidence_threshold', str(request.min_confidence_threshold)))
        
        if request.require_primary_citations is not None:
            updates.append(('require_primary_citations', str(request.require_primary_citations).lower()))
        
        if request.block_uncited_suggestions is not None:
            updates.append(('block_uncited_suggestions', str(request.block_uncited_suggestions).lower()))
        
        for key, value in updates:
            db.execute("""
                INSERT OR REPLACE INTO explainability_config (config_key, config_value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))
        
        db.commit()
        
        # Update citation engine configuration
        await response_processor.update_citation_requirements({
            "min_citations": request.min_citations_required,
            "min_confidence": request.min_confidence_threshold
        })
        
        return {"status": "updated", "changes": len(updates)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update validation config: {str(e)}")

# Analysis and Reporting Endpoints
@router.get("/analysis/response/{response_id}")
async def get_response_analysis(
    response_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis for a specific response"""
    try:
        # Get response details
        response_result = db.execute("""
            SELECT response_id, query, response_text, model_name, model_version, 
                   confidence_score, created_at, lpa_code, is_valid, is_blocked
            FROM ai_responses WHERE response_id = ?
        """, (response_id,)).fetchone()
        
        if not response_result:
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Get citations
        citations_result = db.execute("""
            SELECT citation_id, citation_type, citation_quality, title, authority,
                   citation_date, url, section_reference, relevance_score, 
                   content_excerpt, context_explanation
            FROM citations WHERE response_id = ?
        """, (response_id,)).fetchall()
        
        # Get reasoning chain
        reasoning_result = db.execute("""
            SELECT step_number, reasoning_step
            FROM reasoning_chains WHERE response_id = ?
            ORDER BY step_number
        """, (response_id,)).fetchall()
        
        # Get assumptions
        assumptions_result = db.execute("""
            SELECT assumption_text FROM ai_assumptions WHERE response_id = ?
        """, (response_id,)).fetchall()
        
        # Get limitations
        limitations_result = db.execute("""
            SELECT limitation_text FROM ai_limitations WHERE response_id = ?
        """, (response_id,)).fetchall()
        
        # Get LPA context
        lpa_context_result = db.execute("""
            SELECT lpa_code, lpa_name, hdt_score, hdt_status, five_yhls_years,
                   five_yhls_assessment_date, local_plan_adoption_date
            FROM lpa_context_snapshots WHERE response_id = ?
        """, (response_id,)).fetchone()
        
        return {
            "response_id": response_result[0],
            "query": response_result[1],
            "response_text": response_result[2],
            "model_info": {
                "model_name": response_result[3],
                "model_version": response_result[4]
            },
            "confidence_score": response_result[5],
            "created_at": response_result[6],
            "lpa_code": response_result[7],
            "is_valid": bool(response_result[8]),
            "is_blocked": bool(response_result[9]),
            "citations": [
                {
                    "id": row[0],
                    "type": row[1],
                    "quality": row[2],
                    "title": row[3],
                    "authority": row[4],
                    "date": row[5],
                    "url": row[6],
                    "section_reference": row[7],
                    "relevance_score": row[8],
                    "content_excerpt": row[9],
                    "context": row[10]
                }
                for row in citations_result
            ],
            "reasoning_chain": [row[1] for row in reasoning_result],
            "assumptions": [row[0] for row in assumptions_result],
            "limitations": [row[0] for row in limitations_result],
            "lpa_context": {
                "lpa_code": lpa_context_result[0],
                "lpa_name": lpa_context_result[1],
                "hdt_score": lpa_context_result[2],
                "hdt_status": lpa_context_result[3],
                "five_yhls_years": lpa_context_result[4],
                "five_yhls_assessment_date": lpa_context_result[5],
                "local_plan_adoption_date": lpa_context_result[6]
            } if lpa_context_result else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get response analysis: {str(e)}")

@router.get("/analysis/statistics")
async def get_explainability_statistics(
    days: int = Query(7, description="Number of days to analyze"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get explainability statistics"""
    try:
        since_date = datetime.now() - timedelta(days=days)
        
        # Overall response statistics
        response_stats = db.execute("""
            SELECT 
                COUNT(*) as total_responses,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as valid_responses,
                SUM(CASE WHEN is_blocked = 1 THEN 1 ELSE 0 END) as blocked_responses,
                AVG(confidence_score) as avg_confidence
            FROM ai_responses 
            WHERE created_at > ?
        """, (since_date,)).fetchone()
        
        # Citation statistics
        citation_stats = db.execute("""
            SELECT 
                citation_quality,
                COUNT(*) as count
            FROM citations c
            JOIN ai_responses r ON c.response_id = r.response_id
            WHERE r.created_at > ?
            GROUP BY citation_quality
        """, (since_date,)).fetchall()
        
        # Model performance
        model_stats = db.execute("""
            SELECT 
                model_name,
                model_version,
                COUNT(*) as responses,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) as valid_count
            FROM ai_responses
            WHERE created_at > ?
            GROUP BY model_name, model_version
        """, (since_date,)).fetchall()
        
        # LPA distribution
        lpa_stats = db.execute("""
            SELECT 
                lpa_code,
                COUNT(*) as responses
            FROM ai_responses
            WHERE created_at > ? AND lpa_code IS NOT NULL
            GROUP BY lpa_code
            ORDER BY responses DESC
            LIMIT 10
        """, (since_date,)).fetchall()
        
        return {
            "period_days": days,
            "overall_statistics": {
                "total_responses": response_stats[0],
                "valid_responses": response_stats[1],
                "blocked_responses": response_stats[2],
                "average_confidence": round(response_stats[3], 3) if response_stats[3] else 0,
                "validation_rate": round(response_stats[1] / response_stats[0], 3) if response_stats[0] > 0 else 0
            },
            "citation_statistics": {
                row[0]: row[1] for row in citation_stats
            },
            "model_performance": [
                {
                    "model_name": row[0],
                    "model_version": row[1],
                    "responses": row[2],
                    "average_confidence": round(row[3], 3),
                    "validation_rate": round(row[4] / row[2], 3) if row[2] > 0 else 0
                }
                for row in model_stats
            ],
            "top_lpas": [
                {"lpa_code": row[0], "responses": row[1]}
                for row in lpa_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/blocked-responses")
async def get_blocked_responses(
    limit: int = Query(50, description="Maximum number of results"),
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get list of blocked responses"""
    try:
        blocked_result = db.execute("""
            SELECT response_id, query, block_reason, blocked_at, lpa_code
            FROM blocked_responses
            ORDER BY blocked_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        
        return {
            "blocked_responses": [
                {
                    "response_id": row[0],
                    "query": row[1],
                    "block_reason": row[2],
                    "blocked_at": row[3],
                    "lpa_code": row[4]
                }
                for row in blocked_result
            ],
            "total": len(blocked_result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blocked responses: {str(e)}")

@router.post("/export/report")
async def export_explainability_report(
    request: ExplainabilityReportRequest,
    current_user = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export comprehensive explainability report"""
    try:
        # Get response analysis
        response_analysis = await get_response_analysis(request.response_id, current_user, db)
        
        # Get analysis snapshot if available
        snapshot_result = db.execute("""
            SELECT snapshot_data FROM analysis_snapshots WHERE response_id = ?
        """, (request.response_id,)).fetchone()
        
        report = {
            "report_id": f"explainability_report_{request.response_id}",
            "generated_at": datetime.now().isoformat(),
            "response_analysis": response_analysis,
            "analysis_snapshot": json.loads(snapshot_result[0]) if snapshot_result else None,
            "report_metadata": {
                "include_full_analysis": request.include_full_analysis,
                "generated_by": current_user.get('user_id'),
                "export_format": "json"
            }
        }
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export report: {str(e)}")

# Health and Status Endpoints
@router.get("/health")
async def get_explainability_health(
    current_user = Depends(get_current_user)
):
    """Get explainability system health"""
    try:
        stats = response_processor.get_processing_statistics()
        
        return {
            "status": "healthy",
            "citation_engine": {
                "index_size": stats["citation_engine_stats"]["index_size"],
                "requirements": {
                    "min_citations": stats["citation_engine_stats"]["min_citations_required"],
                    "min_confidence": stats["citation_engine_stats"]["min_confidence_threshold"]
                }
            },
            "processing_statistics": {
                "total_processed": stats["total_processed"],
                "blocked_responses": stats["blocked_responses"]
            },
            "system_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "system_timestamp": datetime.now().isoformat()
        }