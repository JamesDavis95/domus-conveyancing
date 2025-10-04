"""
AI Response Processor with Explainability
Processes AI responses through citation engine and enforces explainability requirements
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json
import asyncio
from pathlib import Path

from .citation_engine import CitationEngine, AIResponse, ModelVersion, Citation, CitationType, CitationQuality

logger = logging.getLogger(__name__)

class AIResponseProcessor:
    """Main processor for AI responses with explainability enforcement"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.citation_engine = CitationEngine(knowledge_base_path)
        self.blocked_responses = []
        self.response_cache = {}
        
    async def process_ai_response(
        self,
        query: str,
        raw_response: str,
        model_info: Dict[str, Any],
        lpa_code: str = None,
        user_context: Dict[str, Any] = None
    ) -> Tuple[bool, AIResponse, Dict[str, Any]]:
        """
        Process AI response through explainability pipeline
        Returns: (is_valid, processed_response, processing_result)
        """
        
        try:
            # Create model version info
            model_version = ModelVersion(
                model_name=model_info.get('model_name', 'unknown'),
                version=model_info.get('version', '1.0'),
                provider=model_info.get('provider', 'unknown'),
                training_cutoff=datetime.fromisoformat(model_info.get('training_cutoff', '2024-01-01T00:00:00')),
                capabilities=model_info.get('capabilities', []),
                temperature=model_info.get('temperature', 0.7),
                max_tokens=model_info.get('max_tokens', 2000)
            )
            
            # Extract reasoning components from response
            reasoning_components = await self._extract_reasoning_components(raw_response)
            
            # Find relevant citations
            citations = self.citation_engine.find_citations(query, lpa_code)
            
            # Create AI response object
            ai_response = AIResponse(
                response_id="",  # Will be auto-generated
                query=query,
                response_text=raw_response,
                model_version=model_version,
                citations=citations,
                confidence_score=reasoning_components.get('confidence_score', 0.7),
                reasoning_chain=reasoning_components.get('reasoning_chain', []),
                assumptions=reasoning_components.get('assumptions', []),
                limitations=reasoning_components.get('limitations', []),
                alternative_interpretations=reasoning_components.get('alternative_interpretations', []),
                created_at=datetime.now()
            )
            
            # Enhance with LPA context if provided
            if lpa_code:
                ai_response = self.citation_engine.enhance_with_lpa_context(ai_response, lpa_code)
            
            # Validate response
            validation_result = self.citation_engine.validate_ai_response(ai_response)
            
            # Check if suggestions should be blocked
            should_block = self.citation_engine.block_uncited_suggestion(
                ai_response.response_text, 
                ai_response.citations
            )
            
            # Create analysis snapshot
            self.citation_engine.create_analysis_snapshot(ai_response)
            
            # Process result
            processing_result = {
                "validation": validation_result,
                "blocked": should_block,
                "citation_count": len(ai_response.citations),
                "explainability_score": validation_result.get('explainability_score', 0.0),
                "processing_time": datetime.now().isoformat()
            }
            
            if should_block:
                self.blocked_responses.append({
                    "response_id": ai_response.response_id,
                    "query": query,
                    "reason": "Insufficient citations for suggestion",
                    "blocked_at": datetime.now().isoformat()
                })
                
                # Return blocked response
                blocked_response = await self._create_citation_request_response(query, lpa_code)
                return False, blocked_response, processing_result
            
            if not validation_result["valid"]:
                logger.warning(f"Invalid AI response: {validation_result['errors']}")
                
                # Return enhanced response with warnings
                enhanced_response = await self._enhance_response_with_explainability(ai_response)
                return False, enhanced_response, processing_result
            
            # Valid response - enhance with explainability
            enhanced_response = await self._enhance_response_with_explainability(ai_response)
            return True, enhanced_response, processing_result
            
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            
            # Return error response
            error_response = await self._create_error_response(query, str(e))
            return False, error_response, {"error": str(e)}
    
    async def _extract_reasoning_components(self, response_text: str) -> Dict[str, Any]:
        """Extract reasoning components from AI response text"""
        # This would use NLP/pattern matching to extract reasoning elements
        # For now, return mock components
        
        components = {
            "confidence_score": 0.75,
            "reasoning_chain": [
                "Analyzed query for planning policy relevance",
                "Identified applicable national and local planning policies",
                "Considered site-specific constraints and opportunities",
                "Evaluated against current development plan policies",
                "Assessed likely planning authority position"
            ],
            "assumptions": [
                "Current local plan policies remain in force",
                "No recent appeal decisions materially change guidance",
                "Site information provided is accurate and current"
            ],
            "limitations": [
                "Analysis based on publicly available information",
                "Site-specific surveys may reveal additional constraints",
                "Planning policy interpretation may vary between officers"
            ],
            "alternative_interpretations": [
                "Alternative design approach might address concerns",
                "Different policy interpretation possible on borderline cases"
            ]
        }
        
        # In a real implementation, would parse response text to extract these
        return components
    
    async def _create_citation_request_response(self, query: str, lpa_code: str) -> AIResponse:
        """Create response requesting additional citations"""
        
        blocked_response_text = f"""
I cannot provide specific recommendations for this planning query without proper citations to support my advice.

To provide you with reliable guidance, I need to reference:
- Relevant planning policy documents
- Case law or appeal decisions
- Current local plan policies for {lpa_code if lpa_code else 'your area'}
- Up-to-date Housing Delivery Test and 5-year housing land supply data

Please ensure your query includes specific policy references or allow me to search for relevant citations before providing recommendations.

For general information without specific recommendations, I can discuss:
- General planning principles
- Procedural requirements
- Types of considerations typically relevant

Would you like me to search for relevant policy guidance for your area, or would you prefer to provide specific policy references?
        """.strip()
        
        model_version = ModelVersion(
            model_name="citation_enforcement",
            version="1.0",
            provider="domus",
            training_cutoff=datetime.now(),
            capabilities=["citation_enforcement"],
            temperature=0.0,
            max_tokens=500
        )
        
        return AIResponse(
            response_id="",
            query=query,
            response_text=blocked_response_text,
            model_version=model_version,
            citations=[],
            confidence_score=1.0,
            reasoning_chain=["Blocked response due to insufficient citations"],
            assumptions=["User requires cited recommendations"],
            limitations=["Cannot provide uncited advice"],
            alternative_interpretations=[],
            created_at=datetime.now()
        )
    
    async def _create_error_response(self, query: str, error: str) -> AIResponse:
        """Create error response for processing failures"""
        
        error_response_text = f"""
I encountered an error while processing your planning query. This may be due to:

- Temporary system issues
- Complex query requiring manual review  
- Missing data sources for your area

Error details: {error}

Please try rephrasing your query or contact support if this issue persists.
        """.strip()
        
        model_version = ModelVersion(
            model_name="error_handler",
            version="1.0", 
            provider="domus",
            training_cutoff=datetime.now(),
            capabilities=["error_handling"],
            temperature=0.0,
            max_tokens=200
        )
        
        return AIResponse(
            response_id="",
            query=query,
            response_text=error_response_text,
            model_version=model_version,
            citations=[],
            confidence_score=0.0,
            reasoning_chain=["Processing error occurred"],
            assumptions=[],
            limitations=["Unable to process query"],
            alternative_interpretations=[],
            created_at=datetime.now()
        )
    
    async def _enhance_response_with_explainability(self, response: AIResponse) -> AIResponse:
        """Enhance response with explainability components"""
        
        # Add citation section to response
        if response.citations:
            citation_section = "\n\n**Sources and References:**\n"
            for i, citation in enumerate(response.citations, 1):
                citation_display = self.citation_engine.format_citation_display(citation)
                citation_section += f"{i}. {citation_display}\n"
            
            response.response_text += citation_section
        
        # Add confidence and limitations if not already present
        if not any("confidence" in response.response_text.lower() for _ in [1]):
            confidence_section = f"\n\n**Analysis Confidence:** {response.confidence_score:.0%}"
            
            if response.limitations:
                confidence_section += "\n\n**Important Limitations:**\n"
                for limitation in response.limitations:
                    confidence_section += f"• {limitation}\n"
            
            response.response_text += confidence_section
        
        # Add LPA context if available
        if response.lpa_context:
            lpa_section = f"\n\n**Local Context for {response.lpa_context.get('lpa_name')}:**\n"
            
            hdt_data = response.lpa_context.get('hdt_data', {})
            if hdt_data:
                lpa_section += f"• Housing Delivery Test: {hdt_data.get('housing_delivery_test_score')}% ({hdt_data.get('status', 'unknown').title()})\n"
            
            yhls_data = response.lpa_context.get('five_yhls_data', {})
            if yhls_data:
                lpa_section += f"• Five Year Housing Land Supply: {yhls_data.get('five_year_supply')} years\n"
            
            response.response_text += lpa_section
        
        return response
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "total_processed": len(self.response_cache),
            "blocked_responses": len(self.blocked_responses),
            "citation_engine_stats": {
                "index_size": len(self.citation_engine.citation_index),
                "min_citations_required": self.citation_engine.min_citations_required,
                "min_confidence_threshold": self.citation_engine.min_confidence_threshold
            }
        }
    
    async def update_citation_requirements(self, config: Dict[str, Any]):
        """Update citation engine configuration"""
        if "min_citations" in config:
            self.citation_engine.min_citations_required = config["min_citations"]
        
        if "min_confidence" in config:
            self.citation_engine.min_confidence_threshold = config["min_confidence"]
        
        logger.info(f"Updated citation requirements: {config}")

class ExplainabilityMiddleware:
    """Middleware to integrate explainability into existing AI pipelines"""
    
    def __init__(self, processor: AIResponseProcessor):
        self.processor = processor
    
    async def __call__(self, ai_function):
        """Decorator/middleware for AI functions"""
        async def wrapper(*args, **kwargs):
            # Extract query and context from arguments
            query = kwargs.get('query') or (args[0] if args else "")
            lpa_code = kwargs.get('lpa_code')
            
            # Call original AI function
            raw_response = await ai_function(*args, **kwargs)
            
            # Process through explainability pipeline
            is_valid, processed_response, processing_result = await self.processor.process_ai_response(
                query=query,
                raw_response=raw_response.get('response', raw_response) if isinstance(raw_response, dict) else raw_response,
                model_info=raw_response.get('model_info', {}) if isinstance(raw_response, dict) else {},
                lpa_code=lpa_code
            )
            
            # Return enhanced response
            return {
                "response": processed_response.response_text,
                "citations": [self.processor.citation_engine.format_citation_display(c) for c in processed_response.citations],
                "explainability": {
                    "confidence_score": processed_response.confidence_score,
                    "reasoning_chain": processed_response.reasoning_chain,
                    "assumptions": processed_response.assumptions,
                    "limitations": processed_response.limitations
                },
                "lpa_context": processed_response.lpa_context,
                "processing_result": processing_result,
                "valid": is_valid
            }
        
        return wrapper