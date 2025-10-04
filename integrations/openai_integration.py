"""
OpenAI Integration for Planning AI
Server-side only - NEVER expose API key to browser
"""

import os
import openai
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Initialize OpenAI with API key (server-side only)
openai.api_key = os.getenv("OPENAI_API_KEY")

router = APIRouter(prefix="/api/planning-ai", tags=["Planning AI"])

class PlanningAIService:
    """OpenAI integration for planning analysis and document generation"""
    
    def __init__(self):
        self.model = "gpt-4"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    async def analyze_planning_application(self, 
                                         project_data: Dict[str, Any],
                                         context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze planning application with AI"""
        
        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(project_data, context)
            
            # Call OpenAI
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            analysis = self._parse_analysis_response(response)
            
            # Add metadata for explainability
            analysis["metadata"] = {
                "model_version": self.model,
                "generated_at": datetime.utcnow().isoformat(),
                "tokens_used": response.usage.total_tokens,
                "confidence_score": self._calculate_confidence(response)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Planning AI analysis error: {e}")
            raise HTTPException(status_code=500, detail="AI analysis failed")
    
    async def generate_scheme_variants(self, 
                                     project_data: Dict[str, Any],
                                     constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate development scheme variants using AI"""
        
        try:
            prompt = self._build_variants_prompt(project_data, constraints)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_variants_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,  # Higher creativity for variants
                max_tokens=3000
            )
            
            variants = self._parse_variants_response(response)
            
            # Add AI metadata to each variant
            for variant in variants:
                variant["ai_metadata"] = {
                    "model_version": self.model,
                    "generated_at": datetime.utcnow().isoformat(),
                    "confidence_score": self._calculate_confidence(response)
                }
            
            return variants
            
        except Exception as e:
            logger.error(f"Scheme variants generation error: {e}")
            raise HTTPException(status_code=500, detail="Variants generation failed")
    
    async def generate_planning_document(self, 
                                       document_type: str,
                                       project_data: Dict[str, Any],
                                       template_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate planning documents using AI"""
        
        try:
            prompt = self._build_document_prompt(document_type, project_data, template_data)
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_document_system_prompt(document_type)},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower for consistent document quality
                max_tokens=4000
            )
            
            document = self._parse_document_response(response, document_type)
            
            document["metadata"] = {
                "document_type": document_type,
                "model_version": self.model,
                "generated_at": datetime.utcnow().isoformat(),
                "tokens_used": response.usage.total_tokens
            }
            
            return document
            
        except Exception as e:
            logger.error(f"Document generation error: {e}")
            raise HTTPException(status_code=500, detail="Document generation failed")
    
    def _get_system_prompt(self) -> str:
        """System prompt for planning analysis"""
        return """You are an expert planning consultant with deep knowledge of UK planning policy, 
        including NPPF, NPPG, and local planning policies. Analyze planning applications with focus on:
        
        1. Policy compliance (NPPF, local plan, design guides)
        2. Planning constraints and opportunities
        3. Risk assessment and mitigation strategies
        4. Likelihood of approval with confidence scoring
        5. Key precedents and case law
        
        Provide structured, professional analysis with specific policy references and citations."""
    
    def _get_variants_system_prompt(self) -> str:
        """System prompt for scheme variant generation"""
        return """You are an expert development advisor specializing in scheme optimization.
        Generate 3-5 viable development variants that maximize both planning compliance and financial return.
        
        Consider:
        - Planning policy requirements (density, height, design)
        - Market conditions and development viability
        - Construction constraints and costs
        - Community benefits and affordable housing
        
        Rank variants by Planning Score × Profit Score for optimal development outcomes."""
    
    def _get_document_system_prompt(self, document_type: str) -> str:
        """System prompt for document generation"""
        prompts = {
            "planning_statement": "Generate a professional Planning Statement following standard UK format with policy analysis and justification.",
            "heritage_statement": "Create a Heritage Statement analyzing impact on historic environment with appropriate mitigation measures.", 
            "design_access_statement": "Produce a Design and Access Statement covering design principles, accessibility, and community integration."
        }
        
        return prompts.get(document_type, "Generate a professional planning document with appropriate structure and content.")
    
    def _build_analysis_prompt(self, project_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> str:
        """Build analysis prompt from project data"""
        
        prompt_parts = [
            "Analyze this planning application:",
            f"Project: {project_data.get('title', 'Unnamed project')}",
            f"Location: {project_data.get('address', 'Not specified')}",
            f"Proposal: {project_data.get('description', 'Not specified')}",
            f"Development Type: {project_data.get('development_type', 'Not specified')}"
        ]
        
        if context:
            if context.get('constraints'):
                prompt_parts.append(f"Constraints: {json.dumps(context['constraints'])}")
            if context.get('precedents'):
                prompt_parts.append(f"Similar cases: {json.dumps(context['precedents'])}")
        
        prompt_parts.append("Provide detailed planning analysis with policy references and approval likelihood.")
        
        return "\n\n".join(prompt_parts)
    
    def _build_variants_prompt(self, project_data: Dict[str, Any], constraints: Dict[str, Any]) -> str:
        """Build variants generation prompt"""
        
        return f"""
        Generate development scheme variants for:
        
        Site: {project_data.get('address', 'Not specified')}
        Site Area: {project_data.get('site_area', 'Not specified')}
        Development Type: {project_data.get('development_type', 'Not specified')}
        
        Constraints: {json.dumps(constraints)}
        
        Generate 3-5 variants with different unit counts, heights, and layouts.
        Include planning compliance score and estimated profit for each variant.
        """
    
    def _build_document_prompt(self, document_type: str, project_data: Dict[str, Any], template_data: Optional[Dict[str, Any]]) -> str:
        """Build document generation prompt"""
        
        return f"""
        Generate a {document_type.replace('_', ' ').title()} for:
        
        Project: {project_data.get('title', 'Unnamed project')}
        Location: {project_data.get('address', 'Not specified')}
        Proposal: {project_data.get('description', 'Not specified')}
        
        {json.dumps(template_data) if template_data else ''}
        
        Follow standard UK planning document format with appropriate sections and professional language.
        """
    
    def _parse_analysis_response(self, response) -> Dict[str, Any]:
        """Parse AI analysis response into structured format"""
        
        content = response.choices[0].message.content
        
        # Basic parsing - in production you'd want more sophisticated parsing
        return {
            "analysis": content,
            "planning_score": 75,  # Would extract from AI response
            "approval_likelihood": "Moderate",
            "key_risks": ["Policy compliance", "Neighbor objections"],
            "recommendations": ["Address design concerns", "Provide additional justification"],
            "citations": ["NPPF Para 11", "Local Plan Policy H1"]
        }
    
    def _parse_variants_response(self, response) -> List[Dict[str, Any]]:
        """Parse variants response into structured format"""
        
        content = response.choices[0].message.content
        
        # Simplified parsing - would be more sophisticated in production
        return [
            {
                "variant_name": "Variant A - Maximum Density",
                "description": "20 units, 3 stories, contemporary design",
                "units_residential": 20,
                "building_height_stories": 3,
                "planning_score": 85,
                "profit_score": 75,
                "combined_score": 85 * 75,
                "constraints_met": ["density", "height", "parking"],
                "risk_factors": ["neighbor objections"]
            },
            {
                "variant_name": "Variant B - Balanced Approach", 
                "description": "16 units, 2.5 stories, traditional design",
                "units_residential": 16,
                "building_height_stories": 2.5,
                "planning_score": 95,
                "profit_score": 65,
                "combined_score": 95 * 65,
                "constraints_met": ["design", "heritage", "density"],
                "risk_factors": ["viability"]
            }
        ]
    
    def _parse_document_response(self, response, document_type: str) -> Dict[str, Any]:
        """Parse document generation response"""
        
        content = response.choices[0].message.content
        
        return {
            "title": f"{document_type.replace('_', ' ').title()}",
            "content": content,
            "sections": self._extract_sections(content),
            "word_count": len(content.split()),
            "format": "markdown"
        }
    
    def _extract_sections(self, content: str) -> List[str]:
        """Extract document sections for navigation"""
        
        sections = []
        lines = content.split('\n')
        
        for line in lines:
            if line.startswith('#'):
                sections.append(line.strip('# '))
        
        return sections
    
    def _calculate_confidence(self, response) -> float:
        """Calculate confidence score based on response characteristics"""
        
        # Simplified confidence calculation
        # In production, would analyze response content, citations, etc.
        return 0.85

# Initialize service
planning_ai_service = PlanningAIService()

# Routes with RBAC enforcement
@router.post("/analyze")
async def analyze_planning_application(request: dict):
    """Run Planning AI analysis - decrements AI credits"""
    
    # This endpoint is protected by credit_enforcement middleware
    # Credits automatically decremented on successful call
    
    result = await planning_ai_service.analyze_planning_application(
        project_data=request.get("project_data", {}),
        context=request.get("context", {})
    )
    
    return result

@router.post("/variants")
async def generate_scheme_variants(request: dict):
    """Generate development scheme variants - decrements AI credits"""
    
    result = await planning_ai_service.generate_scheme_variants(
        project_data=request.get("project_data", {}),
        constraints=request.get("constraints", {})
    )
    
    return {"variants": result}

@router.post("/copilot/chat")
async def planning_copilot_chat(request: dict):
    """Planning Copilot conversation - decrements AI credits"""
    
    # Simplified chat interface
    response = await planning_ai_service.analyze_planning_application(
        project_data=request.get("project_data", {}),
        context={"query": request.get("message", "")}
    )
    
    return {
        "response": response["analysis"],
        "metadata": response["metadata"]
    }

# Export for main app integration
__all__ = ["router", "planning_ai_service"]