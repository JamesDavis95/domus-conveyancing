"""
Document Generation Orchestrator
Main interface for AI-powered document generation
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
import uuid

from ..planning_ai.schemas import SiteInput, Constraint, Score, Recommendation
from .planning_statement import generate_planning_statement
from .design_access import generate_design_access_statement
from .templates import (
    TemplateEngine, DocumentType, OutputFormat,
    generate_document_from_template, get_available_templates
)


class DocumentGenerator:
    """Main document generation orchestrator"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.supported_documents = {
            'planning_statement': self._generate_planning_statement,
            'design_access_statement': self._generate_design_access_statement,
            'heritage_statement': self._generate_heritage_statement,
            'transport_statement': self._generate_transport_statement,
            'ecology_statement': self._generate_ecology_statement,
            'cover_letter': self._generate_cover_letter
        }
    
    async def generate_document(
        self,
        document_type: str,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None,
        output_format: OutputFormat = OutputFormat.HTML
    ) -> Dict[str, Any]:
        """
        Generate a planning document using AI analysis
        
        Args:
            document_type: Type of document to generate
            site_input: Site and development details
            constraints: Planning constraints identified
            score: AI approval probability score  
            recommendations: Improvement recommendations
            custom_options: Custom options and content
            output_format: Desired output format
            
        Returns:
            Generated document with metadata
        """
        
        if document_type not in self.supported_documents:
            raise ValueError(f"Unsupported document type: {document_type}")
        
        # Generate document content
        generator_func = self.supported_documents[document_type]
        document_content = await generator_func(
            site_input, constraints, score, recommendations, custom_options
        )
        
        # Format document using template engine
        if document_type in ['planning_statement', 'design_access_statement']:
            template_name = document_type
            formatted_document = await generate_document_from_template(
                template_name,
                document_content['sections'],
                {
                    'site': site_input,
                    'constraints': constraints,
                    'score': score,
                    'recommendations': recommendations,
                    'generation_date': datetime.now().strftime('%d %B %Y'),
                    'custom_options': custom_options or {}
                },
                output_format
            )
        else:
            # For other document types, return structured content
            formatted_document = {
                'document': document_content,
                'template_name': document_type,
                'output_format': output_format.value,
                'metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'word_count': self._calculate_word_count(document_content),
                }
            }
        
        # Add generation metadata
        formatted_document['generation_id'] = str(uuid.uuid4())
        formatted_document['ai_analysis'] = {
            'approval_probability': score.probability,
            'constraints_identified': len(constraints),
            'recommendations_count': len(recommendations)
        }
        
        return formatted_document
    
    async def generate_document_package(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        document_types: List[str],
        output_format: OutputFormat = OutputFormat.HTML
    ) -> Dict[str, Any]:
        """
        Generate a package of multiple related documents
        
        Args:
            site_input: Site and development details
            constraints: Planning constraints
            score: AI scoring results
            recommendations: AI recommendations
            document_types: List of document types to generate
            output_format: Desired output format
            
        Returns:
            Package containing all generated documents
        """
        
        # Generate documents in parallel
        generation_tasks = []
        for doc_type in document_types:
            if doc_type in self.supported_documents:
                task = self.generate_document(
                    doc_type, site_input, constraints, score, 
                    recommendations, None, output_format
                )
                generation_tasks.append((doc_type, task))
        
        # Wait for all documents to be generated
        generated_documents = {}
        for doc_type, task in generation_tasks:
            try:
                document = await task
                generated_documents[doc_type] = document
            except Exception as e:
                generated_documents[doc_type] = {
                    'error': str(e),
                    'status': 'failed'
                }
        
        # Create document package
        package = {
            'package_id': str(uuid.uuid4()),
            'site_address': site_input.address,
            'generated_at': datetime.utcnow().isoformat(),
            'documents': generated_documents,
            'ai_analysis': {
                'approval_probability': score.probability,
                'confidence': score.confidence,
                'key_constraints': [c.type for c in constraints[:5]],
                'top_recommendations': [r.description for r in recommendations[:3]]
            },
            'summary': {
                'total_documents': len(document_types),
                'successful_generations': len([d for d in generated_documents.values() if 'error' not in d]),
                'total_word_count': sum(
                    d.get('metadata', {}).get('word_count', 0) 
                    for d in generated_documents.values() 
                    if 'error' not in d
                )
            }
        }
        
        return package
    
    async def _generate_planning_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate planning statement"""
        
        return await generate_planning_statement(
            site_input, constraints, score, recommendations,
            custom_options.get('custom_content') if custom_options else None
        )
    
    async def _generate_design_access_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate design & access statement"""
        
        return await generate_design_access_statement(
            site_input, constraints, score, recommendations,
            custom_options.get('design_data') if custom_options else None
        )
    
    async def _generate_heritage_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate heritage statement"""
        
        # Filter heritage-related constraints
        heritage_constraints = [c for c in constraints if c.category == 'heritage']
        
        heritage_statement = {
            'title': f'Heritage Statement: {site_input.address}',
            'sections': {
                'introduction': {
                    'title': 'Introduction',
                    'content': f'''
                    This Heritage Statement has been prepared to accompany a planning application for 
                    {site_input.development_type.lower()} development at {site_input.address}.

                    The purpose of this statement is to assess the significance of heritage assets 
                    that may be affected by the proposed development and to demonstrate that the 
                    development will preserve or enhance their significance.
                    '''
                },
                'heritage_assessment': {
                    'title': 'Heritage Assessment',
                    'content': self._generate_heritage_assessment_content(
                        site_input, heritage_constraints
                    )
                },
                'impact_assessment': {
                    'title': 'Impact Assessment',
                    'content': self._generate_heritage_impact_content(
                        site_input, heritage_constraints, recommendations
                    )
                },
                'conclusion': {
                    'title': 'Conclusion',
                    'content': f'''
                    The proposed development has been carefully designed to preserve the significance 
                    of heritage assets in the area. The development will make a positive contribution 
                    to the character and appearance of the area.
                    '''
                }
            },
            'metadata': {
                'generated_by': 'Domus Planning AI',
                'heritage_constraints_count': len(heritage_constraints),
                'ai_score': score.probability
            }
        }
        
        return heritage_statement
    
    async def _generate_transport_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate transport statement"""
        
        # Filter transport-related constraints
        transport_constraints = [c for c in constraints if c.category == 'transport']
        
        transport_statement = {
            'title': f'Transport Statement: {site_input.address}',
            'sections': {
                'introduction': {
                    'title': 'Introduction',
                    'content': f'''
                    This Transport Statement has been prepared to assess the transport implications 
                    of the proposed {site_input.development_type.lower()} development at {site_input.address}.
                    '''
                },
                'existing_conditions': {
                    'title': 'Existing Transport Conditions',
                    'content': self._generate_transport_conditions_content(site_input)
                },
                'development_proposals': {
                    'title': 'Development Proposals',
                    'content': f'''
                    The proposed development comprises {site_input.proposal_description or '[description to be added]'}.
                    
                    **Trip Generation**
                    The development is expected to generate [X] vehicle movements per day.
                    
                    **Parking Provision**
                    Parking provision is made in accordance with local standards.
                    '''
                },
                'impact_assessment': {
                    'title': 'Transport Impact Assessment',
                    'content': self._generate_transport_impact_content(transport_constraints, recommendations)
                },
                'mitigation_measures': {
                    'title': 'Mitigation Measures',
                    'content': self._generate_transport_mitigation_content(recommendations)
                }
            }
        }
        
        return transport_statement
    
    async def _generate_ecology_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate ecology statement"""
        
        # Filter ecology-related constraints
        ecology_constraints = [c for c in constraints if c.category == 'ecology']
        
        ecology_statement = {
            'title': f'Ecological Assessment: {site_input.address}',
            'sections': {
                'introduction': {
                    'title': 'Introduction',
                    'content': f'''
                    This Ecological Assessment has been prepared to identify potential ecological 
                    constraints and opportunities associated with the proposed development at {site_input.address}.
                    '''
                },
                'baseline_ecology': {
                    'title': 'Baseline Ecological Conditions',
                    'content': self._generate_ecology_baseline_content(site_input, ecology_constraints)
                },
                'impact_assessment': {
                    'title': 'Ecological Impact Assessment',
                    'content': self._generate_ecology_impact_content(ecology_constraints)
                },
                'mitigation_enhancement': {
                    'title': 'Mitigation and Enhancement',
                    'content': self._generate_ecology_mitigation_content(recommendations)
                },
                'biodiversity_net_gain': {
                    'title': 'Biodiversity Net Gain',
                    'content': '''
                    The development will deliver measurable biodiversity net gain through:
                    - Native tree and shrub planting
                    - Wildlife-friendly landscaping
                    - Bird and bat box installation
                    - Sustainable drainage features
                    '''
                }
            }
        }
        
        return ecology_statement
    
    async def _generate_cover_letter(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        custom_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate planning application cover letter"""
        
        cover_letter = {
            'title': f'Planning Application Cover Letter: {site_input.address}',
            'content': f'''
            Dear Planning Officer,

            **Planning Application: {site_input.address}**
            **Proposal:** {site_input.proposal_description or '[Development description]'}

            I write to submit a planning application for the above development on behalf of 
            {site_input.applicant_details.get('name', '[Applicant name]') if site_input.applicant_details else '[Applicant name]'}.

            **Application Summary**

            The application seeks planning permission for {site_input.development_type.lower()} development 
            comprising {site_input.proposal_description or '[detailed description to be added]'}.

            **Supporting Documents**

            The application is supported by the following documents:
            - Completed application forms and certificates
            - Location plan (1:1250 scale)
            - Site plan and proposed plans
            - Elevations and sections
            - Planning Statement
            - Design and Access Statement
            {self._list_additional_documents(constraints)}

            **Key Planning Considerations**

            The main planning considerations are:
            {self._summarise_key_considerations(constraints, score)}

            **AI Planning Analysis**

            Our AI planning analysis indicates an approval probability of {score.probability:.1f}%, 
            reflecting strong policy compliance and appropriate mitigation of constraints.

            **Recommendation**

            The proposed development represents high quality, sustainable development that accords 
            with the development plan. We respectfully request that the Local Planning Authority 
            grants planning permission.

            Please contact the undersigned if you require any additional information or clarification.

            Yours faithfully,

            [Agent Name]
            [Company]
            [Contact Details]
            ''',
            'metadata': {
                'generated_by': 'Domus Planning AI',
                'ai_score': score.probability
            }
        }
        
        return cover_letter
    
    # Helper methods for content generation
    
    def _generate_heritage_assessment_content(
        self,
        site_input: SiteInput,
        heritage_constraints: List[Constraint]
    ) -> str:
        """Generate heritage assessment content"""
        
        if not heritage_constraints:
            return '''
            A desktop assessment has been undertaken to identify heritage assets in the vicinity 
            of the site. No significant heritage constraints have been identified that would 
            affect the proposed development.
            '''
        
        content_parts = []
        content_parts.append("**Heritage Assets Identified:**")
        
        for constraint in heritage_constraints:
            content_parts.append(f"- {constraint.description}")
        
        content_parts.append("\n**Significance Assessment:**")
        content_parts.append(
            "The heritage assets have been assessed for their significance in accordance "
            "with Historic England guidance."
        )
        
        return '\n'.join(content_parts)
    
    def _generate_heritage_impact_content(
        self,
        site_input: SiteInput,
        heritage_constraints: List[Constraint],
        recommendations: List[Recommendation]
    ) -> str:
        """Generate heritage impact content"""
        
        if not heritage_constraints:
            return "No significant heritage impacts are anticipated from the proposed development."
        
        content_parts = []
        for constraint in heritage_constraints:
            content_parts.append(f"**Impact on {constraint.type}:**")
            content_parts.append(constraint.impact)
            content_parts.append(f"*Mitigation:* {constraint.mitigation_measures}")
            content_parts.append("")
        
        return '\n'.join(content_parts)
    
    def _generate_transport_conditions_content(self, site_input: SiteInput) -> str:
        """Generate transport conditions content"""
        
        return f'''
        **Site Location and Access**
        
        The site is located at {site_input.address} and is currently accessed via 
        {site_input.access_details or '[access details to be confirmed]'}.

        **Highway Network**
        
        The local highway network comprises [description of local roads and traffic conditions].

        **Public Transport**
        
        The site benefits from [public transport accessibility assessment].

        **Pedestrian and Cycle Facilities**
        
        Existing pedestrian and cycle facilities in the area include [description of facilities].
        '''
    
    def _generate_transport_impact_content(
        self,
        transport_constraints: List[Constraint],
        recommendations: List[Recommendation]
    ) -> str:
        """Generate transport impact content"""
        
        if not transport_constraints:
            return "The proposed development is not expected to have any significant transport impacts."
        
        content_parts = []
        for constraint in transport_constraints:
            content_parts.append(f"**{constraint.type}:** {constraint.impact}")
        
        return '\n'.join(content_parts)
    
    def _generate_transport_mitigation_content(self, recommendations: List[Recommendation]) -> str:
        """Generate transport mitigation content"""
        
        transport_recommendations = [
            r for r in recommendations 
            if any(word in r.description.lower() for word in ['transport', 'traffic', 'parking', 'access'])
        ]
        
        if not transport_recommendations:
            return "No specific transport mitigation measures are required."
        
        mitigation_items = [f"- {rec.description}" for rec in transport_recommendations]
        return '\n'.join(mitigation_items)
    
    def _generate_ecology_baseline_content(
        self,
        site_input: SiteInput,
        ecology_constraints: List[Constraint]
    ) -> str:
        """Generate ecology baseline content"""
        
        content = f'''
        **Site Description**
        
        The site comprises approximately {site_input.site_area or '[area to be confirmed]'} 
        and currently consists of {site_input.existing_use or '[existing habitat description]'}.

        **Habitats Present**
        
        The following habitats have been identified on site:
        '''
        
        if ecology_constraints:
            for constraint in ecology_constraints:
                content += f"- {constraint.description}\n"
        else:
            content += "- [Habitat survey results to be added]\n"
        
        return content
    
    def _generate_ecology_impact_content(self, ecology_constraints: List[Constraint]) -> str:
        """Generate ecology impact content"""
        
        if not ecology_constraints:
            return "No significant ecological impacts are anticipated from the proposed development."
        
        content_parts = []
        for constraint in ecology_constraints:
            content_parts.append(f"**{constraint.type}:** {constraint.impact}")
        
        return '\n'.join(content_parts)
    
    def _generate_ecology_mitigation_content(self, recommendations: List[Recommendation]) -> str:
        """Generate ecology mitigation content"""
        
        ecology_recommendations = [
            r for r in recommendations 
            if any(word in r.description.lower() for word in ['ecology', 'biodiversity', 'wildlife', 'habitat'])
        ]
        
        if not ecology_recommendations:
            return '''
            Standard mitigation measures will include:
            - Timing of works to avoid breeding bird season
            - Native species planting
            - Wildlife-friendly lighting design
            '''
        
        mitigation_items = [f"- {rec.description}" for rec in ecology_recommendations]
        return '\n'.join(mitigation_items)
    
    def _list_additional_documents(self, constraints: List[Constraint]) -> str:
        """List additional documents based on constraints"""
        
        additional_docs = []
        
        constraint_categories = set(c.category for c in constraints)
        
        if 'heritage' in constraint_categories:
            additional_docs.append("- Heritage Statement")
        if 'transport' in constraint_categories:
            additional_docs.append("- Transport Statement")
        if 'ecology' in constraint_categories:
            additional_docs.append("- Ecological Assessment")
        if 'flood_risk' in constraint_categories:
            additional_docs.append("- Flood Risk Assessment")
        
        return '\n' + '\n'.join(additional_docs) if additional_docs else ''
    
    def _summarise_key_considerations(self, constraints: List[Constraint], score: Score) -> str:
        """Summarise key planning considerations"""
        
        if not constraints:
            considerations = [
                "- Principle of development",
                "- Design and character",
                "- Residential amenity",
                "- Highway safety"
            ]
        else:
            considerations = [f"- {c.type}" for c in constraints[:5]]
        
        return '\n'.join(considerations)
    
    def _calculate_word_count(self, content: Any) -> int:
        """Calculate word count for various content formats"""
        
        if isinstance(content, dict):
            if 'sections' in content:
                total_words = 0
                for section in content['sections'].values():
                    if isinstance(section, dict) and 'content' in section:
                        total_words += len(section['content'].split())
                return total_words
            elif 'content' in content:
                return len(content['content'].split())
        elif isinstance(content, str):
            return len(content.split())
        
        return 0


# Singleton document generator instance
document_generator = DocumentGenerator()


# Convenience functions
async def generate_planning_document(
    document_type: str,
    site_input: SiteInput,
    constraints: List[Constraint],
    score: Score,
    recommendations: List[Recommendation],
    output_format: OutputFormat = OutputFormat.HTML
) -> Dict[str, Any]:
    """Generate a single planning document"""
    
    return await document_generator.generate_document(
        document_type, site_input, constraints, score, 
        recommendations, None, output_format
    )


async def generate_planning_document_package(
    site_input: SiteInput,
    constraints: List[Constraint],
    score: Score,
    recommendations: List[Recommendation],
    document_types: Optional[List[str]] = None,
    output_format: OutputFormat = OutputFormat.HTML
) -> Dict[str, Any]:
    """Generate a complete package of planning documents"""
    
    if document_types is None:
        document_types = ['planning_statement', 'design_access_statement', 'cover_letter']
    
    return await document_generator.generate_document_package(
        site_input, constraints, score, recommendations, 
        document_types, output_format
    )


def get_supported_document_types() -> List[str]:
    """Get list of supported document types"""
    
    return list(document_generator.supported_documents.keys())