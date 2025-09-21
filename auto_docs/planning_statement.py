"""
Planning Statement Generator
AI-powered generation of comprehensive Planning Statements
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from ..planning_ai.schemas import SiteInput, Constraint, Score, Recommendation
from .templates import TemplateEngine, DocumentTemplate


class PlanningStatementGenerator:
    """Generate comprehensive Planning Statements using AI analysis"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.statement_sections = [
            'executive_summary',
            'site_description', 
            'proposal_description',
            'planning_policy_context',
            'planning_assessment',
            'consultation_strategy',
            'conclusion'
        ]
    
    async def generate_planning_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_content: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive Planning Statement
        
        Args:
            site_input: Site and development details
            constraints: Planning constraints identified
            score: AI approval probability score
            recommendations: Improvement recommendations
            custom_content: Custom content for specific sections
            
        Returns:
            Dictionary containing the generated statement content
        """
        
        # Prepare context data for template generation
        context = {
            'site': site_input,
            'constraints': constraints,
            'score': score,
            'recommendations': recommendations,
            'generation_date': datetime.now().strftime('%d %B %Y'),
            'custom_content': custom_content or {}
        }
        
        # Generate each section
        sections = {}
        for section in self.statement_sections:
            sections[section] = await self._generate_section(section, context)
        
        # Compile final document
        planning_statement = {
            'title': f'Planning Statement: {site_input.address}',
            'reference': site_input.reference or 'TBC',
            'applicant': site_input.applicant_details.get('name', 'TBC') if site_input.applicant_details else 'TBC',
            'agent': site_input.applicant_details.get('agent', 'TBC') if site_input.applicant_details else 'TBC',
            'date': context['generation_date'],
            'sections': sections,
            'appendices': await self._generate_appendices(context),
            'metadata': {
                'generated_by': 'Domus Planning AI',
                'ai_score': score.probability,
                'constraints_count': len(constraints),
                'recommendations_count': len(recommendations),
                'word_count': self._calculate_word_count(sections)
            }
        }
        
        return planning_statement
    
    async def _generate_section(self, section_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for a specific section"""
        
        if section_name == 'executive_summary':
            return await self._generate_executive_summary(context)
        elif section_name == 'site_description':
            return await self._generate_site_description(context)
        elif section_name == 'proposal_description':
            return await self._generate_proposal_description(context)
        elif section_name == 'planning_policy_context':
            return await self._generate_policy_context(context)
        elif section_name == 'planning_assessment':
            return await self._generate_planning_assessment(context)
        elif section_name == 'consultation_strategy':
            return await self._generate_consultation_strategy(context)
        elif section_name == 'conclusion':
            return await self._generate_conclusion(context)
        else:
            return {'title': section_name.replace('_', ' ').title(), 'content': '[Content to be added]'}
    
    async def _generate_executive_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary section"""
        
        site = context['site']
        score = context['score']
        
        template = f"""
        This Planning Statement has been prepared in support of a planning application for {site.development_type.lower()} 
        development at {site.address}.

        The proposal comprises {site.proposal_description or '[description to be added]'}.

        The AI planning analysis indicates an approval probability of {score.probability:.1f}%, 
        suggesting {self._get_probability_assessment(score.probability)}.

        The key planning considerations identified include:
        {self._format_key_considerations(context['constraints'])}

        This statement demonstrates that the proposed development:
        - Complies with relevant planning policies
        - Represents sustainable development
        - Will not cause unacceptable harm to local amenity
        - Makes appropriate provision for infrastructure requirements

        The development is recommended for approval.
        """
        
        return {
            'title': 'Executive Summary',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_site_description(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate site description section"""
        
        site = context['site']
        
        template = f"""
        **Site Location and Context**
        
        The application site is located at {site.address}. The site coordinates are 
        {site.coordinates[0]:.6f}, {site.coordinates[1]:.6f}.

        **Site Characteristics**
        
        The site comprises approximately {site.site_area or '[area to be confirmed]'} and is currently 
        {site.existing_use or 'in existing use'}.

        **Surrounding Context**
        
        The site is situated within {self._describe_local_character(site)}. The surrounding area is 
        characterised by {self._describe_surroundings(context)}.

        **Access and Transport**
        
        The site is accessed via {site.access_details or '[access details to be added]'}. 
        Public transport accessibility is {self._assess_transport_links(site)}.

        **Constraints and Designations**
        
        {self._describe_site_constraints(context['constraints'])}
        """
        
        return {
            'title': 'Site Description and Context',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_proposal_description(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate proposal description section"""
        
        site = context['site']
        
        template = f"""
        **Development Proposal**
        
        The application seeks planning permission for {site.development_type.lower()} development 
        comprising {site.proposal_description or '[detailed description to be added]'}.

        **Scale and Design**
        
        The proposed development will provide:
        {self._format_development_schedule(site)}

        **Design Approach**
        
        The design has been developed to:
        - Respond positively to the local character and context
        - Provide high quality accommodation
        - Maximise energy efficiency and sustainability
        - Ensure appropriate relationship with neighbouring properties

        **Materials and Appearance**
        
        The proposed materials palette includes {self._describe_materials(site)}, 
        selected to complement the local vernacular while providing a contemporary interpretation.

        **Landscaping**
        
        The landscape strategy provides {self._describe_landscaping(site)}.
        """
        
        return {
            'title': 'Proposal Description',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_policy_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate planning policy context section"""
        
        template = f"""
        **National Planning Policy**
        
        The National Planning Policy Framework (NPPF) sets out the Government's planning policies 
        for England. Key relevant sections include:
        
        - Section 5: Delivering a sufficient supply of homes
        - Section 11: Making effective use of land  
        - Section 12: Achieving well-designed places
        - Section 15: Conserving and enhancing the natural environment

        **Local Planning Policy**
        
        The development plan comprises:
        {self._identify_local_plan_policies(context)}

        **Relevant Policies**
        
        The key policies relevant to this application include:
        {self._list_relevant_policies(context)}

        **Supplementary Planning Documents**
        
        Relevant supplementary planning guidance includes:
        {self._identify_spd_guidance(context)}

        **Material Considerations**
        
        Other material considerations include:
        - Planning Practice Guidance
        - Appeal decisions and case law
        - Emerging policy (where relevant)
        """
        
        return {
            'title': 'Planning Policy Context',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_planning_assessment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate planning assessment section"""
        
        constraints = context['constraints']
        recommendations = context['recommendations']
        
        # Group constraints by category for structured assessment
        constraint_categories = {}
        for constraint in constraints:
            category = constraint.category
            if category not in constraint_categories:
                constraint_categories[category] = []
            constraint_categories[category].append(constraint)
        
        assessment_sections = []
        
        for category, category_constraints in constraint_categories.items():
            section_content = f"""
            **{category.replace('_', ' ').title()}**
            
            {self._assess_constraint_category(category, category_constraints, recommendations)}
            """
            assessment_sections.append(section_content)
        
        # Add general assessment topics if no specific constraints identified
        if not constraints:
            default_topics = [
                'Principle of Development',
                'Design and Character',  
                'Residential Amenity',
                'Highway Safety',
                'Infrastructure and Services'
            ]
            
            for topic in default_topics:
                section_content = f"""
                **{topic}**
                
                {self._generate_default_assessment(topic, context)}
                """
                assessment_sections.append(section_content)
        
        return {
            'title': 'Planning Assessment',
            'content': self._clean_template_text('\n'.join(assessment_sections))
        }
    
    async def _generate_consultation_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate consultation strategy section"""
        
        template = f"""
        **Pre-Application Consultation**
        
        {self._describe_preapp_consultation(context)}

        **Statutory Consultation**
        
        The following statutory consultees will be consulted as part of the planning application process:
        {self._identify_statutory_consultees(context)}

        **Public Consultation**
        
        The local planning authority will undertake public consultation in accordance with their 
        Statement of Community Involvement. This will include:
        
        - Site notices
        - Neighbour notification letters
        - Publication on the planning register
        
        **Community Engagement**
        
        {self._describe_community_engagement(context)}
        """
        
        return {
            'title': 'Consultation Strategy',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_conclusion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conclusion section"""
        
        score = context['score']
        
        template = f"""
        This Planning Statement demonstrates that the proposed development represents a high quality, 
        sustainable form of development that accords with national and local planning policy.

        **Key Benefits**
        
        The development will deliver the following benefits:
        {self._summarise_benefits(context)}

        **Policy Compliance**
        
        The assessment contained within this statement demonstrates compliance with relevant planning 
        policies and guidance.

        **AI Planning Analysis**
        
        The AI planning analysis indicates an approval probability of {score.probability:.1f}%, 
        reflecting {self._interpret_ai_score(score)}.

        **Recommendation**
        
        For the reasons set out in this statement, the proposed development is considered to represent 
        sustainable development that accords with the development plan. The application is recommended 
        for approval {self._suggest_conditions(context)}.

        We respectfully request that the Local Planning Authority grant planning permission for this 
        high-quality development proposal.
        """
        
        return {
            'title': 'Conclusion',
            'content': self._clean_template_text(template)
        }
    
    async def _generate_appendices(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate list of recommended appendices"""
        
        appendices = [
            {'title': 'Location Plan', 'description': '1:1250 scale location plan'},
            {'title': 'Site Plan', 'description': 'Existing and proposed site plans'},
            {'title': 'Floor Plans', 'description': 'Existing and proposed floor plans'},
            {'title': 'Elevations', 'description': 'Existing and proposed elevations'},
        ]
        
        # Add constraint-specific appendices
        constraints = context['constraints']
        for constraint in constraints:
            if constraint.category == 'heritage':
                appendices.append({
                    'title': 'Heritage Statement',
                    'description': 'Assessment of heritage impacts'
                })
            elif constraint.category == 'ecology':
                appendices.append({
                    'title': 'Ecological Assessment',
                    'description': 'Protected species and habitat survey'
                })
            elif constraint.category == 'transport':
                appendices.append({
                    'title': 'Transport Statement',
                    'description': 'Transport and highway impact assessment'
                })
        
        return appendices
    
    # Helper methods for content generation
    
    def _get_probability_assessment(self, probability: float) -> str:
        """Convert probability score to qualitative assessment"""
        if probability >= 80:
            return "a high likelihood of approval"
        elif probability >= 60:
            return "a good prospect of approval"  
        elif probability >= 40:
            return "moderate prospects, subject to addressing key issues"
        else:
            return "significant challenges that require careful consideration"
    
    def _format_key_considerations(self, constraints: List[Constraint]) -> str:
        """Format key planning considerations"""
        if not constraints:
            return "- No significant constraints identified"
        
        considerations = []
        for constraint in constraints[:5]:  # Top 5 constraints
            considerations.append(f"- {constraint.description}")
        
        return '\n'.join(considerations)
    
    def _describe_local_character(self, site: SiteInput) -> str:
        """Describe local character context"""
        # This would be enhanced with actual local data
        return "a predominantly residential area with mixed architectural styles"
    
    def _describe_surroundings(self, context: Dict[str, Any]) -> str:
        """Describe surrounding context"""
        return "a mixture of residential properties, local services, and green spaces"
    
    def _assess_transport_links(self, site: SiteInput) -> str:
        """Assess transport accessibility"""
        return "good, with regular bus services and proximity to key destinations"
    
    def _describe_site_constraints(self, constraints: List[Constraint]) -> str:
        """Describe planning constraints affecting the site"""
        if not constraints:
            return "The site is not subject to any significant planning constraints."
        
        constraint_text = []
        for constraint in constraints:
            constraint_text.append(f"- {constraint.description} ({constraint.severity})")
        
        return '\n'.join(constraint_text)
    
    def _format_development_schedule(self, site: SiteInput) -> str:
        """Format development schedule/accommodation"""
        if site.development_type == 'RESIDENTIAL':
            return f"- {site.dwelling_count or '[number]'} dwellings\n- Associated parking and amenity space"
        else:
            return f"- [Development schedule to be added]"
    
    def _describe_materials(self, site: SiteInput) -> str:
        """Describe proposed materials"""
        return "[materials to be confirmed - typically brick, render, tile/slate roofing]"
    
    def _describe_landscaping(self, site: SiteInput) -> str:
        """Describe landscaping proposals"""
        return "[landscaping strategy to be confirmed - retention of existing trees where possible, new native planting]"
    
    def _identify_local_plan_policies(self, context: Dict[str, Any]) -> str:
        """Identify relevant local plan"""
        # This would integrate with actual policy database
        return "- [Local Plan name and adoption date]\n- [Neighbourhood Plan if applicable]"
    
    def _list_relevant_policies(self, context: Dict[str, Any]) -> str:
        """List relevant planning policies"""
        # This would be populated from actual policy analysis
        policies = [
            "Policy H1: Housing Development",
            "Policy D1: Design Quality",
            "Policy T1: Transport and Accessibility"
        ]
        return '\n'.join([f"- {policy}" for policy in policies])
    
    def _identify_spd_guidance(self, context: Dict[str, Any]) -> str:
        """Identify relevant SPDs"""
        return "- Design Guide SPD\n- Parking Standards SPD"
    
    def _assess_constraint_category(self, category: str, constraints: List[Constraint], recommendations: List[Recommendation]) -> str:
        """Assess a category of constraints"""
        
        # Find relevant recommendations for this category
        relevant_recommendations = [r for r in recommendations if category in r.description.lower()]
        
        assessment = f"The {category.replace('_', ' ')} considerations for this site include:\n\n"
        
        for constraint in constraints:
            assessment += f"**{constraint.type}**: {constraint.description}\n\n"
            assessment += f"*Impact*: {constraint.impact}\n"
            assessment += f"*Mitigation*: {constraint.mitigation_measures}\n\n"
        
        if relevant_recommendations:
            assessment += "**Recommendations:**\n"
            for rec in relevant_recommendations[:3]:  # Top 3 recommendations
                assessment += f"- {rec.description}\n"
        
        return assessment
    
    def _generate_default_assessment(self, topic: str, context: Dict[str, Any]) -> str:
        """Generate default assessment for standard topics"""
        
        templates = {
            'Principle of Development': "The principle of development is considered acceptable in this location, being consistent with the development plan strategy for the area.",
            'Design and Character': "The proposed design has been carefully developed to respond to local character while providing high quality accommodation.",
            'Residential Amenity': "The development has been designed to ensure no unacceptable impact on the amenity of neighbouring residents.",
            'Highway Safety': "The proposal includes appropriate access arrangements and parking provision in accordance with local standards.",
            'Infrastructure and Services': "The development can be adequately served by existing infrastructure, with appropriate contributions where necessary."
        }
        
        return templates.get(topic, f"The {topic.lower()} aspects of the development are considered acceptable.")
    
    def _describe_preapp_consultation(self, context: Dict[str, Any]) -> str:
        """Describe pre-application consultation"""
        return "Pre-application advice was [sought/not sought] from the Local Planning Authority."
    
    def _identify_statutory_consultees(self, context: Dict[str, Any]) -> str:
        """Identify statutory consultees"""
        consultees = [
            "- Highway Authority",
            "- Environmental Health",
            "- Tree Officer (if applicable)"
        ]
        
        # Add constraint-specific consultees
        for constraint in context['constraints']:
            if constraint.category == 'heritage':
                consultees.append("- Conservation Officer")
            elif constraint.category == 'ecology':
                consultees.append("- Natural England")
        
        return '\n'.join(list(set(consultees)))  # Remove duplicates
    
    def _describe_community_engagement(self, context: Dict[str, Any]) -> str:
        """Describe community engagement"""
        return "[Details of any pre-application community consultation undertaken]"
    
    def _summarise_benefits(self, context: Dict[str, Any]) -> str:
        """Summarise development benefits"""
        site = context['site']
        
        benefits = []
        if site.development_type == 'RESIDENTIAL':
            benefits.append("- Additional housing to meet local needs")
            benefits.append("- Economic benefits during construction")
        
        benefits.extend([
            "- High quality design contributing to local character",
            "- Sustainable development incorporating energy efficiency measures"
        ])
        
        return '\n'.join(benefits)
    
    def _interpret_ai_score(self, score: Score) -> str:
        """Interpret AI confidence score"""
        if score.probability >= 80:
            return "strong policy compliance and limited constraints"
        elif score.probability >= 60:
            return "good policy alignment with manageable issues"
        else:
            return "areas requiring careful consideration and potentially additional supporting information"
    
    def _suggest_conditions(self, context: Dict[str, Any]) -> str:
        """Suggest appropriate conditions"""
        return "subject to appropriate conditions relating to implementation timescales, materials, and landscaping"
    
    def _clean_template_text(self, text: str) -> str:
        """Clean up template text formatting"""
        import re
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _calculate_word_count(self, sections: Dict[str, Dict[str, Any]]) -> int:
        """Calculate approximate word count"""
        total_words = 0
        for section in sections.values():
            content = section.get('content', '')
            total_words += len(content.split())
        
        return total_words


# Main generation function
async def generate_planning_statement(
    site_input: SiteInput,
    constraints: List[Constraint],
    score: Score,
    recommendations: List[Recommendation],
    custom_content: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive Planning Statement
    
    Main entry point for planning statement generation
    """
    
    generator = PlanningStatementGenerator()
    return await generator.generate_planning_statement(
        site_input, constraints, score, recommendations, custom_content
    )