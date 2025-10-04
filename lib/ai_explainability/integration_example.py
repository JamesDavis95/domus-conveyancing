"""
AI Explainability Integration Example
Shows how to integrate explainability with existing AI endpoints
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, Any
import asyncio
from datetime import datetime

from lib.ai_explainability.response_processor import AIResponseProcessor, ExplainabilityMiddleware

# Initialize explainability components
response_processor = AIResponseProcessor()
explainability_middleware = ExplainabilityMiddleware(response_processor)

# Example: Integrating with planning AI endpoint
async def enhanced_planning_ai_analysis(
    query: str,
    property_details: Dict[str, Any],
    lpa_code: str,
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhanced planning AI analysis with explainability enforcement
    """
    
    # Simulate original AI response (would be actual AI model call)
    mock_ai_response = f"""
    Based on the planning query regarding {property_details.get('address', 'the property')}, 
    I recommend considering the following planning factors:

    1. **Policy Compliance**: The proposal should align with local plan policies, 
       particularly regarding residential development in this area.

    2. **Design Considerations**: Ensure the development respects the character 
       and appearance of the surrounding area as required by planning policy.

    3. **Transport Impact**: Consider parking provision and highway safety 
       implications of the proposed development.

    The likelihood of planning permission being granted appears moderate to high, 
    subject to addressing these key considerations.
    """
    
    model_info = {
        "model_name": "planning-ai-v2",
        "version": "2024.3",
        "provider": "domus",
        "training_cutoff": "2024-01-01T00:00:00",
        "capabilities": ["planning_analysis", "policy_interpretation"],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # Process through explainability pipeline
    is_valid, processed_response, processing_result = await response_processor.process_ai_response(
        query=query,
        raw_response=mock_ai_response,
        model_info=model_info,
        lpa_code=lpa_code,
        user_context=user_context
    )
    
    # Return enhanced response with explainability
    return {
        "analysis": processed_response.response_text,
        "explainability": {
            "response_id": processed_response.response_id,
            "is_valid": is_valid,
            "confidence_score": processed_response.confidence_score,
            "reasoning_chain": processed_response.reasoning_chain,
            "assumptions": processed_response.assumptions,
            "limitations": processed_response.limitations,
            "alternative_interpretations": processed_response.alternative_interpretations
        },
        "citations": [
            {
                "title": c.title,
                "authority": c.authority,
                "date": c.date.isoformat(),
                "url": c.url,
                "relevance_score": c.relevance_score,
                "context": c.context
            }
            for c in processed_response.citations
        ],
        "lpa_context": processed_response.lpa_context,
        "processing_metadata": {
            "validation_passed": is_valid,
            "citation_count": len(processed_response.citations),
            "processing_time": processing_result.get("processing_time"),
            "blocked": processing_result.get("blocked", False)
        }
    }

# Example: Using manual integration (since decorator is complex for demo)
async def planning_recommendation_ai(query: str, lpa_code: str = None) -> Dict[str, Any]:
    """
    Planning recommendation AI with manual explainability integration
    """
    # This would be replaced with actual AI model call
    raw_response = f"Based on planning considerations for {lpa_code or 'your area'}, I recommend considering local plan policies and national guidance."
    
    model_info = {
        "model_name": "planning-recommendation-ai",
        "version": "1.0",
        "provider": "domus",
        "training_cutoff": "2024-01-01T00:00:00",
        "capabilities": ["recommendations"],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    # Process through explainability
    is_valid, processed_response, processing_result = await response_processor.process_ai_response(
        query=query,
        raw_response=raw_response,
        model_info=model_info,
        lpa_code=lpa_code
    )
    
    return {
        "response": processed_response.response_text,
        "citations": [response_processor.citation_engine.format_citation_display(c) for c in processed_response.citations],
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

# Example: Manual validation of user-provided AI responses
async def validate_external_ai_response(
    ai_response_text: str,
    original_query: str,
    model_provider: str = "external"
) -> Dict[str, Any]:
    """
    Validate AI responses from external sources
    """
    
    model_info = {
        "model_name": model_provider,
        "version": "unknown",
        "provider": "external",
        "training_cutoff": "2024-01-01T00:00:00",
        "capabilities": ["unknown"],
        "temperature": 0.0,
        "max_tokens": 0
    }
    
    is_valid, processed_response, processing_result = await response_processor.process_ai_response(
        query=original_query,
        raw_response=ai_response_text,
        model_info=model_info
    )
    
    return {
        "validation_result": {
            "is_valid": is_valid,
            "blocked": processing_result.get("blocked", False),
            "errors": processing_result["validation"].get("errors", []),
            "warnings": processing_result["validation"].get("warnings", [])
        },
        "required_improvements": [
            "Add citations to support recommendations",
            "Include confidence assessment",
            "Document key assumptions",
            "Acknowledge limitations"
        ] if not is_valid else [],
        "citation_requirements": {
            "minimum_citations": response_processor.citation_engine.min_citations_required,
            "minimum_confidence": response_processor.citation_engine.min_confidence_threshold,
            "required_qualities": ["primary", "secondary"]
        }
    }

# Example usage for testing
async def test_explainability_integration():
    """Test the explainability integration"""
    
    print("🧪 Testing AI Explainability Integration")
    print("=" * 50)
    
    # Test 1: Enhanced planning analysis
    print("\n1. Testing enhanced planning analysis...")
    result1 = await enhanced_planning_ai_analysis(
        query="Can I build a two-story extension on my Victorian terrace house?",
        property_details={"address": "123 Victorian Street, Conservation Area"},
        lpa_code="E06000001",
        user_context={"user_type": "homeowner"}
    )
    
    print(f"   ✅ Analysis completed with {len(result1['citations'])} citations")
    print(f"   ✅ Confidence score: {result1['explainability']['confidence_score']:.2f}")
    print(f"   ✅ Validation passed: {result1['processing_metadata']['validation_passed']}")
    
    # Test 2: Decorator pattern
    print("\n2. Testing decorator pattern...")
    result2 = await planning_recommendation_ai(
        query="What are the chances of getting planning permission for a loft conversion?",
        lpa_code="E06000002"
    )
    
    print(f"   ✅ Enhanced response generated")
    print(f"   ✅ Citations included: {len(result2.get('citations', []))}")
    
    # Test 3: External response validation
    print("\n3. Testing external response validation...")
    external_response = "You should definitely build your extension. It will be approved easily."
    
    result3 = await validate_external_ai_response(
        ai_response_text=external_response,
        original_query="Can I build an extension?",
        model_provider="external_ai"
    )
    
    print(f"   ✅ Validation completed")
    print(f"   ✅ Response valid: {result3['validation_result']['is_valid']}")
    print(f"   ✅ Required improvements: {len(result3['required_improvements'])}")
    
    print("\n🎉 All explainability tests completed successfully!")
    
    return {
        "test_1": result1,
        "test_2": result2, 
        "test_3": result3
    }

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_explainability_integration())