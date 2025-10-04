"""
Planning Copilot - Conversational AI for Planning Guidance
Provides AI-powered guidance grounded on project data, legislation, and planning precedents
"""

from typing import Dict, List, Optional, Any, Tuple, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
import re
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CopilotMode(Enum):
    """Different modes of copilot operation"""
    PLANNING_ADVICE = "planning_advice"
    POLICY_GUIDANCE = "policy_guidance"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_REVIEW = "strategy_review"
    PRECEDENT_SEARCH = "precedent_search"
    DOCUMENT_REVIEW = "document_review"
    QUICK_QUESTION = "quick_question"

class ConversationRole(Enum):
    """Roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConfidenceLevel(Enum):
    """Confidence levels for AI responses"""
    HIGH = "high"        # 80-100% confident
    MEDIUM = "medium"    # 60-79% confident  
    LOW = "low"          # 40-59% confident
    UNCERTAIN = "uncertain"  # <40% confident

@dataclass
class ConversationMessage:
    """A message in a copilot conversation"""
    id: str
    role: ConversationRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class CopilotResponse:
    """Response from Planning Copilot"""
    message: str
    confidence: ConfidenceLevel
    sources: List[str]
    suggestions: List[str]
    warnings: List[str]
    follow_up_questions: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProjectContext:
    """Project context for grounded responses"""
    project_id: str
    project_name: str
    location: str
    development_type: str
    stage: str
    unit_count: Optional[int] = None
    site_area: Optional[float] = None
    planning_status: Optional[str] = None
    constraints: List[str] = None
    planning_history: List[Dict] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []
        if self.planning_history is None:
            self.planning_history = []

@dataclass
class KnowledgeBase:
    """Planning knowledge base for grounding"""
    legislation: Dict[str, Any]
    policies: Dict[str, Any]
    precedents: List[Dict[str, Any]]
    guidance_notes: Dict[str, Any]
    case_studies: List[Dict[str, Any]]
    
    def __post_init__(self):
        if not hasattr(self, 'legislation'):
            self.legislation = {}
        if not hasattr(self, 'policies'):
            self.policies = {}
        if not hasattr(self, 'precedents'):
            self.precedents = []
        if not hasattr(self, 'guidance_notes'):
            self.guidance_notes = {}
        if not hasattr(self, 'case_studies'):
            self.case_studies = []

class PlanningKnowledgeBase:
    """Repository of planning knowledge for AI grounding"""
    
    def __init__(self):
        self.knowledge = self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> KnowledgeBase:
        """Initialize with planning knowledge"""
        
        # Core planning legislation
        legislation = {
            "nppf": {
                "title": "National Planning Policy Framework",
                "key_sections": {
                    "housing": "Delivering a sufficient supply of homes",
                    "design": "Achieving well-designed places",
                    "heritage": "Conserving and enhancing the historic environment",
                    "climate": "Meeting the challenge of climate change"
                },
                "url": "https://www.gov.uk/government/publications/national-planning-policy-framework--2"
            },
            "town_country_planning_act": {
                "title": "Town and Country Planning Act 1990",
                "key_provisions": [
                    "Planning permission requirements",
                    "Development definitions",
                    "Enforcement powers",
                    "Appeals process"
                ]
            }
        }
        
        # Planning policies
        policies = {
            "affordable_housing": {
                "typical_requirements": "20-40% depending on local policy",
                "tenure_split": "Usually 70% affordable rent, 30% shared ownership",
                "thresholds": "Usually applies to developments of 10+ units",
                "viability": "Can be reduced if proven unviable"
            },
            "density": {
                "typical_range": "30-50 dwellings per hectare in urban areas",
                "factors": ["Location", "Transport accessibility", "Character", "Infrastructure"],
                "guidance": "Higher densities acceptable near transport hubs"
            },
            "design": {
                "key_principles": ["Character and context", "Public spaces", "Movement", "Nature"],
                "requirements": "Design and Access Statement usually required",
                "standards": "Building for Life 12, Manual for Streets"
            }
        }
        
        # Planning precedents (sample)
        precedents = [
            {
                "reference": "APP/X1355/W/21/3267964",
                "location": "Generic Town",
                "development": "Residential scheme - 25 units",
                "decision": "Allowed",
                "key_issues": ["Density", "Design", "Affordable housing"],
                "inspector_comments": "Well-designed scheme that responds to local character",
                "relevance_keywords": ["residential", "density", "design"]
            },
            {
                "reference": "APP/Y2466/W/21/3278851", 
                "location": "Sample Village",
                "development": "Housing development - 12 houses",
                "decision": "Dismissed",
                "key_issues": ["Heritage impact", "Character"],
                "inspector_comments": "Harmful to conservation area character",
                "relevance_keywords": ["heritage", "conservation", "character"]
            }
        ]
        
        # Guidance notes
        guidance_notes = {
            "pre_application": {
                "benefits": "Early engagement, reduced risk, faster determination",
                "cost": "Typically £500-£5000 depending on complexity",
                "process": "Submit proposal, attend meeting, receive written advice"
            },
            "planning_conditions": {
                "tests": "Necessary, relevant, enforceable, precise, reasonable",
                "common_types": ["Materials", "Landscaping", "Drainage", "Construction management"],
                "discharge": "Submit details for approval before commencement"
            },
            "section_106": {
                "purpose": "Mitigate impact of development",
                "typical_contributions": ["Affordable housing", "Infrastructure", "Community facilities"],
                "negotiation": "Must be directly related to development"
            }
        }
        
        # Case studies
        case_studies = [
            {
                "title": "Urban Brownfield Regeneration",
                "location": "City Centre",
                "challenges": ["Contamination", "Access", "Viability"],
                "solutions": ["Phased development", "Mixed use", "Grant funding"],
                "outcomes": "Successful regeneration delivering 200 homes",
                "lessons": "Early stakeholder engagement critical for complex sites"
            }
        ]
        
        return KnowledgeBase(
            legislation=legislation,
            policies=policies,
            precedents=precedents,
            guidance_notes=guidance_notes,
            case_studies=case_studies
        )
    
    def search_legislation(self, query: str) -> List[Dict[str, Any]]:
        """Search legislation database"""
        results = []
        query_lower = query.lower()
        
        for key, leg in self.knowledge.legislation.items():
            if any(term in leg.get("title", "").lower() for term in query_lower.split()):
                results.append({
                    "type": "legislation",
                    "key": key,
                    "title": leg.get("title"),
                    "relevance": "high",
                    "content": leg
                })
        
        return results
    
    def search_precedents(self, query: str, project_context: Optional[ProjectContext] = None) -> List[Dict[str, Any]]:
        """Search planning precedents"""
        results = []
        query_terms = query.lower().split()
        
        for precedent in self.knowledge.precedents:
            # Check relevance based on keywords and query
            relevance_score = 0
            keywords = precedent.get("relevance_keywords", [])
            
            for term in query_terms:
                if any(term in keyword for keyword in keywords):
                    relevance_score += 1
                if term in precedent.get("development", "").lower():
                    relevance_score += 2
                if term in precedent.get("key_issues", []):
                    relevance_score += 3
            
            # Boost relevance if project context matches
            if project_context:
                if project_context.development_type.lower() in precedent.get("development", "").lower():
                    relevance_score += 2
            
            if relevance_score > 0:
                results.append({
                    "type": "precedent", 
                    "relevance_score": relevance_score,
                    "content": precedent
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_policy_guidance(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get policy guidance for specific topic"""
        return self.knowledge.policies.get(topic.lower())
    
    def get_guidance_note(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get guidance note for specific topic"""
        return self.knowledge.guidance_notes.get(topic.lower())

class PromptTemplate:
    """Templates for AI prompts with project context"""
    
    @staticmethod
    def planning_advice_prompt(question: str, project_context: ProjectContext, 
                             knowledge_results: List[Dict]) -> str:
        """Generate prompt for planning advice"""
        
        context_info = f"""
PROJECT CONTEXT:
- Project: {project_context.project_name}
- Location: {project_context.location}
- Type: {project_context.development_type}
- Stage: {project_context.stage}
- Units: {project_context.unit_count or 'Not specified'}
- Site Area: {project_context.site_area or 'Not specified'} acres
- Constraints: {', '.join(project_context.constraints) if project_context.constraints else 'None specified'}
"""
        
        knowledge_info = ""
        if knowledge_results:
            knowledge_info = "\nRELEVANT KNOWLEDGE:\n"
            for result in knowledge_results[:5]:  # Top 5 results
                knowledge_info += f"- {result.get('type', 'Unknown')}: {result.get('content', {}).get('title', 'No title')}\n"
        
        prompt = f"""You are a senior planning consultant providing expert advice on UK planning matters.

{context_info}

{knowledge_info}

QUESTION: {question}

Please provide practical, actionable advice that:
1. Directly addresses the question
2. Considers the specific project context
3. References relevant planning policy and legislation
4. Identifies potential risks and mitigation strategies
5. Suggests next steps

Be specific, professional, and grounded in current UK planning practice."""
        
        return prompt
    
    @staticmethod
    def risk_assessment_prompt(project_context: ProjectContext, 
                             legislation_changes: List[Dict]) -> str:
        """Generate prompt for risk assessment"""
        
        changes_info = ""
        if legislation_changes:
            changes_info = "\nRECENT LEGISLATION CHANGES:\n"
            for change in legislation_changes[:3]:
                changes_info += f"- {change.get('title', 'Unknown change')}\n"
        
        prompt = f"""You are a planning risk specialist. Assess planning risks for this development project:

PROJECT: {project_context.project_name}
LOCATION: {project_context.location}
TYPE: {project_context.development_type}
STAGE: {project_context.stage}
CONSTRAINTS: {', '.join(project_context.constraints) if project_context.constraints else 'None specified'}

{changes_info}

Provide a comprehensive risk assessment covering:
1. Planning policy compliance risks
2. Technical/design risks
3. Consultation and objection risks  
4. Market/viability risks
5. Programme risks

For each risk, provide:
- Risk level (High/Medium/Low)
- Impact description
- Likelihood assessment
- Mitigation strategies
- Monitoring approach

Focus on actionable insights for risk management."""
        
        return prompt

class ConversationManager:
    """Manages copilot conversations"""
    
    def __init__(self):
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.context_cache: Dict[str, ProjectContext] = {}
    
    def start_conversation(self, conversation_id: str, project_context: ProjectContext) -> str:
        """Start new conversation with project context"""
        self.conversations[conversation_id] = []
        self.context_cache[conversation_id] = project_context
        
        # Add system message
        system_msg = ConversationMessage(
            id=f"{conversation_id}_system",
            role=ConversationRole.SYSTEM,
            content=f"Planning Copilot session started for {project_context.project_name}",
            timestamp=datetime.now(),
            metadata={"project_id": project_context.project_id}
        )
        
        self.conversations[conversation_id].append(system_msg)
        
        logger.info(f"Started conversation {conversation_id} for project {project_context.project_id}")
        
        return conversation_id
    
    def add_message(self, conversation_id: str, role: ConversationRole, content: str) -> ConversationMessage:
        """Add message to conversation"""
        message = ConversationMessage(
            id=f"{conversation_id}_{len(self.conversations.get(conversation_id, []))}",
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append(message)
        return message
    
    def get_conversation_history(self, conversation_id: str) -> List[ConversationMessage]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    def get_project_context(self, conversation_id: str) -> Optional[ProjectContext]:
        """Get project context for conversation"""
        return self.context_cache.get(conversation_id)

class PlanningCopilot:
    """Main Planning Copilot AI system"""
    
    def __init__(self):
        self.knowledge_base = PlanningKnowledgeBase()
        self.conversation_manager = ConversationManager()
        self.templates = PromptTemplate()
        
        # Would integrate with actual AI model (OpenAI, Azure OpenAI, etc.)
        self.ai_client = None
    
    def ask_question(self, conversation_id: str, question: str, 
                    mode: CopilotMode = CopilotMode.PLANNING_ADVICE) -> CopilotResponse:
        """Ask question to Planning Copilot"""
        
        logger.info(f"Processing question in mode {mode.value}: {question[:100]}...")
        
        # Get project context
        project_context = self.conversation_manager.get_project_context(conversation_id)
        if not project_context:
            return CopilotResponse(
                message="No project context found. Please start a new session.",
                confidence=ConfidenceLevel.UNCERTAIN,
                sources=[],
                suggestions=[],
                warnings=["Project context required for accurate advice"],
                follow_up_questions=[]
            )
        
        # Add user message to conversation
        self.conversation_manager.add_message(conversation_id, ConversationRole.USER, question)
        
        # Search knowledge base
        knowledge_results = self._search_knowledge(question, project_context, mode)
        
        # Generate AI response
        response = self._generate_response(question, project_context, knowledge_results, mode)
        
        # Add assistant response to conversation
        self.conversation_manager.add_message(conversation_id, ConversationRole.ASSISTANT, response.message)
        
        logger.info(f"Generated response with confidence: {response.confidence.value}")
        
        return response
    
    def _search_knowledge(self, question: str, project_context: ProjectContext, 
                         mode: CopilotMode) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        
        results = []
        
        # Search legislation
        leg_results = self.knowledge_base.search_legislation(question)
        results.extend(leg_results)
        
        # Search precedents
        precedent_results = self.knowledge_base.search_precedents(question, project_context)
        results.extend(precedent_results)
        
        # Get policy guidance for common topics
        for topic in ["affordable_housing", "density", "design"]:
            if topic in question.lower():
                policy = self.knowledge_base.get_policy_guidance(topic)
                if policy:
                    results.append({
                        "type": "policy",
                        "topic": topic,
                        "content": policy
                    })
        
        return results
    
    def _generate_response(self, question: str, project_context: ProjectContext,
                          knowledge_results: List[Dict], mode: CopilotMode) -> CopilotResponse:
        """Generate AI response (simulated for now)"""
        
        # This would call actual AI model with appropriate prompt
        # For now, simulate intelligent responses based on question content
        
        response_text = self._simulate_ai_response(question, project_context, knowledge_results, mode)
        
        # Extract confidence level based on knowledge available
        confidence = self._assess_confidence(question, knowledge_results)
        
        # Generate sources
        sources = [f"{r.get('type', 'Unknown')}: {r.get('content', {}).get('title', 'Reference')}" 
                  for r in knowledge_results[:3]]
        
        # Generate suggestions
        suggestions = self._generate_suggestions(question, project_context, mode)
        
        # Generate warnings
        warnings = self._identify_warnings(question, project_context)
        
        # Generate follow-up questions
        follow_up_questions = self._generate_follow_ups(question, project_context, mode)
        
        return CopilotResponse(
            message=response_text,
            confidence=confidence,
            sources=sources,
            suggestions=suggestions,
            warnings=warnings,
            follow_up_questions=follow_up_questions,
            metadata={
                "mode": mode.value,
                "project_id": project_context.project_id,
                "knowledge_sources_used": len(knowledge_results)
            }
        )
    
    def _simulate_ai_response(self, question: str, project_context: ProjectContext,
                            knowledge_results: List[Dict], mode: CopilotMode) -> str:
        """Simulate AI response (would be replaced with actual AI call)"""
        
        q_lower = question.lower()
        
        if "affordable housing" in q_lower:
            return f"""For your {project_context.development_type} project in {project_context.location}, affordable housing requirements typically apply to developments of 10+ units.

Based on current policy, you should expect:
- 20-40% affordable housing requirement (check local plan for exact percentage)
- Tenure split usually 70% affordable rent, 30% shared ownership
- On-site provision preferred for schemes over 15 units
- Off-site contribution or reduced percentage may be acceptable if viability proven

Next steps:
1. Check the local planning authority's specific requirements
2. Engage with the housing team early in the process
3. Consider early viability assessment if marginal
4. Discuss affordable housing design integration"""

        elif "density" in q_lower:
            return f"""For your {project_context.unit_count or 'proposed'} unit development, density considerations are crucial for planning success.

Typical density expectations:
- Urban areas: 30-50 dwellings per hectare
- Suburban areas: 20-35 dwellings per hectare  
- Your current proposal: {(project_context.unit_count or 0) / (project_context.site_area or 1):.1f} units per acre

Key factors affecting acceptable density:
- Public transport accessibility
- Local character and context
- Infrastructure capacity
- Design quality and amenity

Recommendations:
1. Review local plan density policies
2. Analyze comparable recent approvals
3. Consider design-led approach to justify density
4. Ensure adequate amenity space provision"""

        elif "design" in q_lower:
            return f"""Design quality is fundamental to planning success for your {project_context.development_type} project.

Key design considerations:
- Local character and context analysis
- Building heights and massing
- Materials and architectural style
- Public spaces and landscaping
- Parking and access arrangements

Requirements likely needed:
- Design and Access Statement
- Heritage Impact Assessment (if applicable)
- Landscape and Visual Impact Assessment
- 3D visualizations or models

Best practice approach:
1. Conduct thorough site and context analysis
2. Engage with planning officers early
3. Consider community consultation
4. Use quality design team with local experience"""

        else:
            return f"""Thank you for your question about {question}. 

For your {project_context.development_type} project in {project_context.location}, I recommend:

1. **Policy Review**: Check the local plan and supplementary planning documents for specific requirements
2. **Pre-application Advice**: Consider formal pre-application discussion with the planning authority
3. **Professional Input**: Engage appropriate specialists (planning consultant, architect, etc.)
4. **Risk Assessment**: Identify and plan for potential planning risks

The planning process can be complex, and early engagement with the local planning authority is usually beneficial for projects at {project_context.stage} stage.

Would you like me to provide more specific guidance on any particular aspect of your project?"""
    
    def _assess_confidence(self, question: str, knowledge_results: List[Dict]) -> ConfidenceLevel:
        """Assess confidence level of response"""
        
        # Simple heuristic based on knowledge availability
        if len(knowledge_results) >= 3:
            return ConfidenceLevel.HIGH
        elif len(knowledge_results) >= 2:
            return ConfidenceLevel.MEDIUM
        elif len(knowledge_results) >= 1:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    def _generate_suggestions(self, question: str, project_context: ProjectContext, mode: CopilotMode) -> List[str]:
        """Generate helpful suggestions"""
        
        suggestions = [
            "Consider pre-application advice meeting",
            "Review recent similar approvals in the area",
            "Engage with local community early"
        ]
        
        if project_context.stage == "pre-application":
            suggestions.extend([
                "Prepare comprehensive Design and Access Statement",
                "Consider planning performance agreement"
            ])
        
        if "affordable housing" in question.lower():
            suggestions.append("Engage affordable housing specialist")
        
        return suggestions
    
    def _identify_warnings(self, question: str, project_context: ProjectContext) -> List[str]:
        """Identify potential warnings"""
        
        warnings = []
        
        if "heritage" in project_context.constraints:
            warnings.append("Heritage constraints may require specialist assessment")
        
        if "conservation area" in project_context.constraints:
            warnings.append("Conservation area location requires careful design consideration")
        
        if project_context.unit_count and project_context.unit_count > 50:
            warnings.append("Major development may require Environmental Impact Assessment")
        
        return warnings
    
    def _generate_follow_ups(self, question: str, project_context: ProjectContext, mode: CopilotMode) -> List[str]:
        """Generate follow-up questions"""
        
        follow_ups = [
            "What are the specific local plan policies for this site?",
            "Have there been any recent planning applications nearby?",
            "What are the main planning risks you're concerned about?"
        ]
        
        if mode == CopilotMode.PLANNING_ADVICE:
            follow_ups.extend([
                "Would you like me to review your planning strategy?",
                "Do you need guidance on pre-application procedures?"
            ])
        
        return follow_ups
    
    def start_session(self, project_context: ProjectContext) -> str:
        """Start new copilot session"""
        
        conversation_id = f"copilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_context.project_id}"
        
        self.conversation_manager.start_conversation(conversation_id, project_context)
        
        logger.info(f"Started Planning Copilot session {conversation_id}")
        
        return conversation_id
    
    def get_session_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of copilot session"""
        
        history = self.conversation_manager.get_conversation_history(conversation_id)
        project_context = self.conversation_manager.get_project_context(conversation_id)
        
        user_messages = [m for m in history if m.role == ConversationRole.USER]
        assistant_messages = [m for m in history if m.role == ConversationRole.ASSISTANT]
        
        return {
            "conversation_id": conversation_id,
            "project_id": project_context.project_id if project_context else None,
            "project_name": project_context.project_name if project_context else None,
            "start_time": history[0].timestamp if history else None,
            "end_time": history[-1].timestamp if history else None,
            "total_messages": len(history),
            "user_questions": len(user_messages),
            "ai_responses": len(assistant_messages),
            "topics_discussed": self._extract_topics(user_messages)
        }
    
    def _extract_topics(self, messages: List[ConversationMessage]) -> List[str]:
        """Extract topics from conversation"""
        
        topics = set()
        topic_keywords = {
            "affordable_housing": ["affordable", "social", "shared ownership"],
            "design": ["design", "appearance", "architecture", "materials"],
            "density": ["density", "units per hectare", "dwellings"],
            "heritage": ["heritage", "conservation", "listed", "historic"],
            "transport": ["transport", "parking", "access", "highway"],
            "environment": ["environment", "ecology", "biodiversity", "flood"]
        }
        
        for message in messages:
            content_lower = message.content.lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topics.add(topic)
        
        return list(topics)

# Helper functions
def create_sample_project_context() -> ProjectContext:
    """Create sample project context for testing"""
    return ProjectContext(
        project_id="PROJ_001",
        project_name="Greenfield Residential Development",
        location="Example Town, County", 
        development_type="residential",
        stage="pre-application",
        unit_count=25,
        site_area=1.5,
        planning_status="planning_required",
        constraints=["flood_zone_2", "conservation_area_nearby"]
    )

# Global copilot instance
planning_copilot = PlanningCopilot()

# Export classes and functions
__all__ = [
    "CopilotMode",
    "ConversationRole", 
    "ConfidenceLevel",
    "ConversationMessage",
    "CopilotResponse",
    "ProjectContext",
    "KnowledgeBase",
    "PlanningKnowledgeBase",
    "PromptTemplate",
    "ConversationManager",
    "PlanningCopilot",
    "planning_copilot",
    "create_sample_project_context"
]