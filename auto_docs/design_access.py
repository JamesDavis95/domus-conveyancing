"""
Design & Access Statement Generator
AI-powered generation of comprehensive Design & Access Statements
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..planning_ai.schemas import SiteInput, Constraint, Score, Recommendation
from .templates import TemplateEngine, DocumentTemplate


class DesignAccessStatementGenerator:
    """Generate comprehensive Design & Access Statements using AI analysis"""
    
    def __init__(self):
        self.template_engine = TemplateEngine()
        self.statement_sections = [
            'introduction',
            'context_appraisal',
            'design_evolution', 
            'design_principles',
            'access_strategy',
            'sustainability',
            'conclusion'
        ]
    
    async def generate_design_access_statement(
        self,
        site_input: SiteInput,
        constraints: List[Constraint],
        score: Score,
        recommendations: List[Recommendation],
        design_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive Design & Access Statement
        
        Args:
            site_input: Site and development details
            constraints: Planning constraints identified  
            score: AI approval probability score
            recommendations: Improvement recommendations
            design_data: Additional design information and images
            
        Returns:
            Dictionary containing the generated D&A statement content
        """
        
        # Prepare context data for template generation
        context = {
            'site': site_input,
            'constraints': constraints,
            'score': score,
            'recommendations': recommendations,
            'design_data': design_data or {},
            'generation_date': datetime.now().strftime('%d %B %Y')
        }
        
        # Generate each section
        sections = {}
        for section in self.statement_sections:
            sections[section] = await self._generate_section(section, context)
        
        # Compile final document
        design_access_statement = {
            'title': f'Design & Access Statement: {site_input.address}',
            'reference': site_input.reference or 'TBC',
            'applicant': site_input.applicant_details.get('name', 'TBC') if site_input.applicant_details else 'TBC',
            'agent': site_input.applicant_details.get('agent', 'TBC') if site_input.applicant_details else 'TBC',
            'date': context['generation_date'],
            'sections': sections,
            'appendices': await self._generate_appendices(context),
            'metadata': {
                'generated_by': 'Domus Planning AI',
                'ai_score': score.probability,
                'word_count': self._calculate_word_count(sections),
                'image_requirements': self._identify_image_requirements(context)
            }
        }
        
        return design_access_statement
    
    async def _generate_section(self, section_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for a specific section"""
        
        if section_name == 'introduction':
            return await self._generate_introduction(context)
        elif section_name == 'context_appraisal':
            return await self._generate_context_appraisal(context)
        elif section_name == 'design_evolution':
            return await self._generate_design_evolution(context)
        elif section_name == 'design_principles':
            return await self._generate_design_principles(context)
        elif section_name == 'access_strategy':
            return await self._generate_access_strategy(context)
        elif section_name == 'sustainability':
            return await self._generate_sustainability(context)
        elif section_name == 'conclusion':
            return await self._generate_conclusion(context)
        else:
            return {'title': section_name.replace('_', ' ').title(), 'content': '[Content to be added]'}
    
    async def _generate_introduction(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate introduction section"""
        
        site = context['site']
        
        template = f"""
        **Purpose and Scope**
        
        This Design and Access Statement has been prepared to accompany a planning application for 
        {site.development_type.lower()} development at {site.address}.

        The statement demonstrates how the design principles and concepts have been applied to the 
        proposed development, and explains the policy context and design process that has informed 
        the scheme.

        **Development Proposal**
        
        The application seeks planning permission for {site.proposal_description or '[description to be added]'}.

        **Statement Structure**
        
        This Design and Access Statement is structured as follows:
        
        - **Context Appraisal**: Analysis of the site and surrounding area
        - **Design Evolution**: Description of the design development process
        - **Design Principles**: Key design principles informing the scheme
        - **Access Strategy**: Approach to accessibility and inclusive design
        - **Sustainability**: Environmental and energy performance measures
        - **Conclusion**: Summary of design achievements

        **Design Team**
        
        The design has been developed by a multidisciplinary team including:
        - Architect: [To be confirmed]
        - Planning Consultant: [To be confirmed]
        - [Other consultants as applicable]
        """
        
        return {
            'title': 'Introduction',
            'content': self._clean_template_text(template),
            'image_refs': ['Site location plan', 'Aerial photograph']
        }
    
    async def _generate_context_appraisal(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate context appraisal section"""
        
        site = context['site']
        constraints = context['constraints']
        
        template = f"""
        **Site Analysis**
        
        The application site is located at {site.address} and comprises approximately 
        {site.site_area or '[area to be confirmed]'}. 

        **Physical Context**
        
        *Topography and Orientation*
        The site {self._describe_topography(site)}. The predominant aspect is {self._describe_aspect(site)}.

        *Existing Buildings and Features*
        {self._describe_existing_features(site)}

        *Boundaries and Edges*
        The site boundaries comprise {self._describe_boundaries(site)}.

        **Urban Context**
        
        *Character Assessment*
        The surrounding area is characterised by {self._analyse_local_character(site, constraints)}.

        *Building Heights and Scale*
        The prevailing building height in the area is {self._analyse_building_heights(site)}. 
        Development density is {self._analyse_density(site)}.

        *Architectural Styles*
        The local architectural character includes {self._analyse_architectural_styles(site)}.

        **Movement and Accessibility**
        
        *Vehicular Access*
        The site is accessed via {site.access_details or '[access details to be added]'}. 
        The local highway network comprises {self._describe_highway_network(site)}.

        *Pedestrian and Cycle Routes*
        {self._analyse_pedestrian_routes(site)}

        *Public Transport*
        Public transport accessibility is {self._analyse_public_transport(site)}.

        **Landscape and Green Infrastructure**
        
        *Existing Vegetation*
        {self._describe_existing_vegetation(site)}

        *Views and Vistas*
        {self._analyse_views_vistas(site)}

        *Green Corridors*
        {self._identify_green_corridors(site)}

        **Constraints and Opportunities**
        
        {self._summarise_design_constraints_opportunities(constraints)}
        """
        
        return {
            'title': 'Context Appraisal',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Context plan showing surrounding development',
                'Character analysis photographs',
                'Topographical survey',
                'Tree survey plan',
                'Views analysis'
            ]
        }
    
    async def _generate_design_evolution(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate design evolution section"""
        
        site = context['site']
        recommendations = context['recommendations']
        
        template = f"""
        **Design Brief and Objectives**
        
        The design brief established the following key objectives:
        {self._define_design_objectives(site, recommendations)}

        **Initial Design Studies**
        
        The design process began with an analysis of the site constraints and opportunities identified 
        in the context appraisal. Initial design studies explored:

        - Alternative site layouts and building positions
        - Massing and scale options
        - Access arrangements  
        - Relationship to neighbouring properties
        - Landscape integration opportunities

        **Option Development**
        
        *Option 1: [Description]*
        {self._describe_design_option(1, site)}

        *Option 2: [Description]*  
        {self._describe_design_option(2, site)}

        *Option 3: [Description]*
        {self._describe_design_option(3, site)}

        **Option Evaluation**
        
        The design options were evaluated against the following criteria:
        {self._define_evaluation_criteria(site, recommendations)}

        **Selected Scheme**
        
        Following the evaluation process, Option [X] was selected as it best meets the design objectives 
        while responding to site constraints and policy requirements.

        The selected scheme incorporates the following key features:
        {self._describe_selected_scheme_features(site)}

        **Refinement Process**
        
        The selected scheme was further refined through:
        {self._describe_refinement_process(recommendations)}
        """
        
        return {
            'title': 'Design Evolution',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Initial design sketches',
                'Site layout options',
                'Massing studies',
                'Design development diagrams'
            ]
        }
    
    async def _generate_design_principles(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate design principles section"""
        
        site = context['site']
        constraints = context['constraints']
        
        template = f"""
        **Overarching Design Philosophy**
        
        The design philosophy for this development is based on creating {self._define_design_philosophy(site)}.

        **Key Design Principles**
        
        **1. Contextual Response**
        {self._describe_contextual_response(site, constraints)}

        **2. Quality and Character**
        {self._describe_quality_character_approach(site)}

        **3. Sustainability and Efficiency**
        {self._describe_sustainability_approach(site)}

        **4. Accessibility and Inclusivity**
        {self._describe_accessibility_approach(site)}

        **5. Landscape Integration**
        {self._describe_landscape_integration(site)}

        **Layout and Massing**
        
        *Site Layout*
        The site layout has been designed to {self._explain_layout_rationale(site)}.

        *Building Massing*
        The building massing responds to {self._explain_massing_rationale(site)}.

        *Orientation and Aspect*
        Buildings are oriented to {self._explain_orientation_rationale(site)}.

        **Architectural Treatment**
        
        *Scale and Proportion*
        {self._describe_scale_proportion(site)}

        *Materials and Detailing*
        The materials palette has been selected to {self._describe_materials_rationale(site)}.

        *Fenestration and Openings*
        {self._describe_fenestration_approach(site)}

        **Public and Private Realm**
        
        *Public Spaces*
        {self._describe_public_realm_strategy(site)}

        *Private Amenity*
        {self._describe_private_amenity_provision(site)}

        *Boundary Treatment*
        {self._describe_boundary_treatment_strategy(site)}
        """
        
        return {
            'title': 'Design Principles',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Design principles diagram',
                'Site layout plan',
                'Building elevations',
                'Materials palette',
                'Landscape strategy plan'
            ]
        }
    
    async def _generate_access_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate access strategy section"""
        
        site = context['site']
        
        template = f"""
        **Inclusive Design Approach**
        
        The development has been designed in accordance with the principles of inclusive design, 
        ensuring that the built environment is accessible and usable by all people regardless of 
        age, disability or other factors.

        **Vehicular Access and Parking**
        
        *Site Access*
        Vehicular access to the site is provided via {self._describe_vehicular_access(site)}.

        *Parking Provision*
        {self._describe_parking_provision(site)}

        *Accessibility Parking*
        Accessible parking spaces are provided in accordance with current standards.

        **Pedestrian Access**
        
        *Site Entrances*
        {self._describe_pedestrian_entrances(site)}

        *Footpath Network*
        {self._describe_footpath_network(site)}

        *Accessibility Features*
        All pedestrian routes incorporate appropriate accessibility features including:
        - Level access where possible
        - Gentle gradients (maximum 1:20)
        - Tactile paving at key decision points
        - Adequate lighting and visibility

        **Building Accessibility**
        
        *Entrance Design*
        {self._describe_building_entrance_accessibility(site)}

        *Internal Circulation*
        {self._describe_internal_accessibility(site)}

        *Accessible Facilities*
        {self._describe_accessible_facilities_provision(site)}

        **Wayfinding and Legibility**
        
        The development incorporates clear wayfinding and legibility measures:
        {self._describe_wayfinding_strategy(site)}

        **Emergency Access**
        
        Emergency vehicle access has been designed to meet the requirements of the local fire authority:
        {self._describe_emergency_access(site)}
        """
        
        return {
            'title': 'Access Strategy',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Access and circulation plan',
                'Accessibility features plan',
                'Parking layout plan',
                'Emergency access plan'
            ]
        }
    
    async def _generate_sustainability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sustainability section"""
        
        site = context['site']
        
        template = f"""
        **Sustainability Strategy**
        
        The development adopts a comprehensive approach to sustainability, addressing environmental, 
        social and economic considerations throughout the design and construction process.

        **Energy Performance**
        
        *Energy Efficiency*
        The development incorporates the following energy efficiency measures:
        {self._describe_energy_efficiency_measures(site)}

        *Renewable Energy*
        Renewable energy provision includes:
        {self._describe_renewable_energy_measures(site)}

        *Carbon Reduction*
        The development will achieve {self._describe_carbon_reduction_targets(site)}.

        **Water Management**
        
        *Water Efficiency*
        Water efficient fixtures and fittings will be installed throughout to reduce consumption.

        *Surface Water Management*
        {self._describe_surface_water_strategy(site)}

        *Rainwater Harvesting*
        {self._describe_rainwater_harvesting(site)}

        **Materials and Waste**
        
        *Sustainable Materials*
        The development will use sustainable materials with low environmental impact:
        {self._describe_sustainable_materials(site)}

        *Waste Minimisation*
        {self._describe_waste_strategy(site)}

        **Biodiversity and Ecology**
        
        *Habitat Creation*
        {self._describe_habitat_creation(site)}

        *Species Protection*
        {self._describe_species_protection_measures(site)}

        *Biodiversity Net Gain*
        {self._describe_biodiversity_net_gain(site)}

        **Climate Resilience**
        
        The development incorporates climate adaptation measures including:
        {self._describe_climate_adaptation_measures(site)}

        **Social Sustainability**
        
        *Community Benefits*
        The development will provide the following community benefits:
        {self._describe_community_benefits(site)}

        *Health and Wellbeing*
        {self._describe_health_wellbeing_measures(site)}
        """
        
        return {
            'title': 'Sustainability',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Sustainability strategy diagram',
                'Energy performance plan',
                'Landscape and ecology plan',
                'Sustainable drainage plan'
            ]
        }
    
    async def _generate_conclusion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate conclusion section"""
        
        site = context['site']
        score = context['score']
        
        template = f"""
        **Design Summary**
        
        This Design and Access Statement demonstrates that the proposed development represents a 
        high quality, contextually appropriate design that responds positively to the site and 
        its surroundings.

        **Key Design Achievements**
        
        The design successfully achieves the following:
        {self._summarise_design_achievements(site)}

        **Policy Compliance**
        
        The design complies with relevant planning policy guidance including:
        - National Planning Policy Framework (Design)
        - Building for a Healthy Life
        - Local design policies and guidance
        - Accessibility standards and regulations

        **AI Design Analysis**
        
        The AI planning analysis indicates an approval probability of {score.probability:.1f}%, 
        reflecting the strength of the design approach and policy compliance.

        **Community Benefits**
        
        The development will provide significant benefits including:
        {self._summarise_community_benefits(site)}

        **Implementation**
        
        The design will be implemented through high quality construction and project management, 
        with appropriate quality control measures to ensure delivery of the design vision.

        **Conclusion**
        
        The proposed development represents exemplary design that will make a positive contribution 
        to the local area. The comprehensive design approach addresses all relevant considerations 
        and demonstrates full compliance with planning policy requirements.

        We are confident that this high quality development merits planning permission and will 
        deliver significant benefits for the local community.
        """
        
        return {
            'title': 'Conclusion',
            'content': self._clean_template_text(template),
            'image_refs': [
                'Final scheme visualisation',
                'Contextual elevation',
                'Landscape perspective'
            ]
        }
    
    async def _generate_appendices(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate list of recommended appendices"""
        
        appendices = [
            {'title': 'Design Drawings', 'description': 'Site plan, floor plans, elevations, sections'},
            {'title': 'Context Analysis', 'description': 'Site photographs and character analysis'},
            {'title': 'Design Development', 'description': 'Option studies and design evolution'},
            {'title': 'Materials Palette', 'description': 'Proposed materials and finishes'},
            {'title': 'Landscape Design', 'description': 'Landscape plans and planting schedule'}
        ]
        
        # Add constraint-specific appendices
        constraints = context['constraints']
        for constraint in constraints:
            if constraint.category == 'heritage':
                appendices.append({
                    'title': 'Heritage Impact Assessment',
                    'description': 'Assessment of impact on heritage assets'
                })
            elif constraint.category == 'ecology':
                appendices.append({
                    'title': 'Ecological Enhancement Plan',
                    'description': 'Biodiversity and habitat enhancement measures'
                })
        
        return appendices
    
    # Helper methods for content generation
    
    def _describe_topography(self, site: SiteInput) -> str:
        """Describe site topography"""
        return "[slopes gently from north to south / is relatively level / has significant level changes]"
    
    def _describe_aspect(self, site: SiteInput) -> str:
        """Describe site aspect"""
        return "[south-facing / east-west orientation / varied aspects]"
    
    def _describe_existing_features(self, site: SiteInput) -> str:
        """Describe existing site features"""
        return f"The site currently contains {site.existing_use or '[existing buildings/features to be described]'}."
    
    def _describe_boundaries(self, site: SiteInput) -> str:
        """Describe site boundaries"""
        return "[mixture of fencing, hedging, and walls / open boundaries / enclosed by mature hedgerow]"
    
    def _analyse_local_character(self, site: SiteInput, constraints: List[Constraint]) -> str:
        """Analyse local character"""
        character_elements = []
        
        # Check for heritage constraints that might inform character
        heritage_constraints = [c for c in constraints if c.category == 'heritage']
        if heritage_constraints:
            character_elements.append("significant heritage value")
        
        # Default character description
        if not character_elements:
            character_elements.append("mixed residential development with varied architectural styles")
        
        return ", ".join(character_elements)
    
    def _analyse_building_heights(self, site: SiteInput) -> str:
        """Analyse prevailing building heights"""
        return "[2 storeys / 2-3 storeys / varied from 1-3 storeys]"
    
    def _analyse_density(self, site: SiteInput) -> str:
        """Analyse development density"""
        return "[low density suburban / medium density residential / mixed density]"
    
    def _analyse_architectural_styles(self, site: SiteInput) -> str:
        """Analyse local architectural styles"""
        return "[Victorian/Edwardian terraces, 1930s semi-detached houses, modern infill development]"
    
    def _describe_highway_network(self, site: SiteInput) -> str:
        """Describe local highway network"""
        return "[quiet residential streets / busy distributor roads / mixture of road types]"
    
    def _analyse_pedestrian_routes(self, site: SiteInput) -> str:
        """Analyse pedestrian routes"""
        return "The site benefits from good pedestrian connectivity with [footways along all frontages / dedicated cycle routes / public rights of way]."
    
    def _analyse_public_transport(self, site: SiteInput) -> str:
        """Analyse public transport accessibility"""
        return "[good with regular bus services / limited but adequate / excellent with multiple transport modes]"
    
    def _describe_existing_vegetation(self, site: SiteInput) -> str:
        """Describe existing vegetation"""
        return "The site contains [mature trees along boundaries / scattered vegetation / limited existing planting]."
    
    def _analyse_views_vistas(self, site: SiteInput) -> str:
        """Analyse views and vistas"""
        return "Key views include [outlook towards countryside / views across neighbouring gardens / enclosed outlook]."
    
    def _identify_green_corridors(self, site: SiteInput) -> str:
        """Identify green corridors"""
        return "The site connects to green infrastructure through [adjacent parkland / tree-lined streets / garden networks]."
    
    def _summarise_design_constraints_opportunities(self, constraints: List[Constraint]) -> str:
        """Summarise design constraints and opportunities"""
        if not constraints:
            return "**Opportunities**: The site presents good opportunities for high quality development with minimal significant constraints."
        
        constraint_summary = "**Key Constraints**:\n"
        for constraint in constraints[:5]:  # Top 5 constraints
            constraint_summary += f"- {constraint.description}\n"
        
        constraint_summary += "\n**Opportunities**:\n- High quality design responding to local character\n- Enhanced landscape and biodiversity\n- Sustainable development principles"
        
        return constraint_summary
    
    def _define_design_objectives(self, site: SiteInput, recommendations: List[Recommendation]) -> str:
        """Define design objectives"""
        objectives = [
            "- Create high quality development appropriate to the local context",
            "- Maximise the development potential of the site",
            "- Ensure no unacceptable impact on neighbouring amenity",
            "- Incorporate sustainable design principles"
        ]
        
        # Add objectives based on recommendations
        for rec in recommendations[:3]:
            if 'design' in rec.description.lower():
                objectives.append(f"- {rec.description}")
        
        return '\n'.join(objectives)
    
    def _describe_design_option(self, option_num: int, site: SiteInput) -> str:
        """Describe a design option"""
        return f"This option explored [layout approach / massing strategy / access arrangement] with [key characteristics]."
    
    def _define_evaluation_criteria(self, site: SiteInput, recommendations: List[Recommendation]) -> str:
        """Define evaluation criteria"""
        criteria = [
            "- Compliance with planning policy",
            "- Impact on local character and amenity", 
            "- Efficiency of site use",
            "- Accessibility and movement",
            "- Sustainability performance"
        ]
        return '\n'.join(criteria)
    
    def _describe_selected_scheme_features(self, site: SiteInput) -> str:
        """Describe selected scheme features"""
        features = [
            "- Appropriate scale and massing for the context",
            "- High quality architectural treatment",
            "- Efficient site layout maximising amenity",
            "- Integrated landscape design"
        ]
        return '\n'.join(features)
    
    def _describe_refinement_process(self, recommendations: List[Recommendation]) -> str:
        """Describe design refinement process"""
        refinements = [
            "- Detailed design development",
            "- Materials selection and specification",
            "- Landscape design integration"
        ]
        
        # Add refinements based on recommendations
        for rec in recommendations[:2]:
            if any(word in rec.description.lower() for word in ['design', 'materials', 'landscape']):
                refinements.append(f"- {rec.description}")
        
        return '\n'.join(refinements)
    
    def _define_design_philosophy(self, site: SiteInput) -> str:
        """Define design philosophy"""
        if site.development_type == 'RESIDENTIAL':
            return "high quality homes that enhance the local character while providing excellent living environments"
        else:
            return "development that positively contributes to the local area while meeting functional requirements"
    
    def _describe_contextual_response(self, site: SiteInput, constraints: List[Constraint]) -> str:
        """Describe contextual response approach"""
        return "The design responds to local context through careful consideration of scale, materials, and layout to ensure integration with the existing townscape."
    
    def _describe_quality_character_approach(self, site: SiteInput) -> str:
        """Describe quality and character approach"""
        return "High quality design is achieved through attention to proportion, materials, and detailing, creating development with distinctive character."
    
    def _describe_sustainability_approach(self, site: SiteInput) -> str:
        """Describe sustainability approach"""
        return "Sustainability is embedded throughout the design through energy efficiency, sustainable materials, and biodiversity enhancement."
    
    def _describe_accessibility_approach(self, site: SiteInput) -> str:
        """Describe accessibility approach"""
        return "Inclusive design principles ensure the development is accessible to all users regardless of age, disability, or mobility."
    
    def _describe_landscape_integration(self, site: SiteInput) -> str:
        """Describe landscape integration"""
        return "Landscape design is fully integrated with the architecture to create a cohesive development that enhances biodiversity."
    
    def _explain_layout_rationale(self, site: SiteInput) -> str:
        """Explain layout rationale"""
        return "optimise the relationship between buildings, create attractive outdoor spaces, and ensure appropriate privacy and amenity"
    
    def _explain_massing_rationale(self, site: SiteInput) -> str:
        """Explain massing rationale"""
        return "the scale and character of surrounding development while creating an appropriate sense of enclosure and definition"
    
    def _explain_orientation_rationale(self, site: SiteInput) -> str:
        """Explain orientation rationale"""
        return "maximise natural light and solar gain while minimising overlooking and ensuring privacy"
    
    def _describe_scale_proportion(self, site: SiteInput) -> str:
        """Describe scale and proportion"""
        return "The scale and proportion of buildings has been carefully considered to ensure compatibility with the local context."
    
    def _describe_materials_rationale(self, site: SiteInput) -> str:
        """Describe materials rationale"""
        return "complement the local vernacular while providing contemporary interpretation using high quality, sustainable materials"
    
    def _describe_fenestration_approach(self, site: SiteInput) -> str:
        """Describe fenestration approach"""
        return "Window design and positioning optimises natural light while ensuring privacy and reflecting local architectural character."
    
    def _describe_public_realm_strategy(self, site: SiteInput) -> str:
        """Describe public realm strategy"""
        return "Public spaces are designed to be attractive, safe, and contribute positively to the streetscene and local environment."
    
    def _describe_private_amenity_provision(self, site: SiteInput) -> str:
        """Describe private amenity provision"""
        if site.development_type == 'RESIDENTIAL':
            return "All dwellings are provided with appropriate private outdoor amenity space in the form of gardens, terraces, or balconies."
        return "Appropriate private amenity space is provided for users of the development."
    
    def _describe_boundary_treatment_strategy(self, site: SiteInput) -> str:
        """Describe boundary treatment strategy"""
        return "Boundary treatments are designed to provide appropriate privacy and security while contributing to the streetscene character."
    
    def _describe_vehicular_access(self, site: SiteInput) -> str:
        """Describe vehicular access"""
        return f"{site.access_details or '[access arrangement to be described]'}"
    
    def _describe_parking_provision(self, site: SiteInput) -> str:
        """Describe parking provision"""
        if site.development_type == 'RESIDENTIAL':
            return f"Parking is provided at {site.parking_spaces or '[number]'} spaces in accordance with local standards."
        return "Appropriate parking provision is made in accordance with local standards."
    
    def _describe_pedestrian_entrances(self, site: SiteInput) -> str:
        """Describe pedestrian entrances"""
        return "Pedestrian entrances are clearly defined, accessible, and integrate well with the streetscene."
    
    def _describe_footpath_network(self, site: SiteInput) -> str:
        """Describe footpath network"""
        return "The internal footpath network provides clear, safe, and convenient routes throughout the development."
    
    def _describe_building_entrance_accessibility(self, site: SiteInput) -> str:
        """Describe building entrance accessibility"""
        return "Building entrances are designed to be fully accessible with level access and appropriate door widths."
    
    def _describe_internal_accessibility(self, site: SiteInput) -> str:
        """Describe internal accessibility"""
        if site.development_type == 'RESIDENTIAL':
            return "Internal layouts comply with accessibility standards with level access and appropriate door widths throughout."
        return "Internal circulation is designed to be fully accessible with appropriate corridor widths and lift access where required."
    
    def _describe_accessible_facilities_provision(self, site: SiteInput) -> str:
        """Describe accessible facilities provision"""
        return "Accessible WC facilities and other amenities are provided in accordance with current standards."
    
    def _describe_wayfinding_strategy(self, site: SiteInput) -> str:
        """Describe wayfinding strategy"""
        return "- Clear sight lines and intuitive layout\n- Appropriate signage and numbering\n- Consistent design vocabulary throughout"
    
    def _describe_emergency_access(self, site: SiteInput) -> str:
        """Describe emergency access"""
        return "Emergency vehicles can access all parts of the development within the required distances and with appropriate access widths."
    
    def _describe_energy_efficiency_measures(self, site: SiteInput) -> str:
        """Describe energy efficiency measures"""
        measures = [
            "- High performance insulation and airtightness",
            "- Energy efficient heating systems", 
            "- LED lighting throughout",
            "- Smart controls and monitoring systems"
        ]
        return '\n'.join(measures)
    
    def _describe_renewable_energy_measures(self, site: SiteInput) -> str:
        """Describe renewable energy measures"""
        return "- Solar photovoltaic panels\n- [Heat pumps / solar thermal / other renewable technologies as applicable]"
    
    def _describe_carbon_reduction_targets(self, site: SiteInput) -> str:
        """Describe carbon reduction targets"""
        return "[specific carbon reduction percentage] compared to Building Regulations baseline through fabric efficiency and renewable energy"
    
    def _describe_surface_water_strategy(self, site: SiteInput) -> str:
        """Describe surface water strategy"""
        return "Surface water runoff will be managed through sustainable drainage systems (SuDS) including [permeable paving / soakaways / attenuation features]."
    
    def _describe_rainwater_harvesting(self, site: SiteInput) -> str:
        """Describe rainwater harvesting"""
        return "Rainwater harvesting systems will be incorporated where feasible to reduce mains water consumption."
    
    def _describe_sustainable_materials(self, site: SiteInput) -> str:
        """Describe sustainable materials"""
        materials = [
            "- Locally sourced materials where possible",
            "- High recycled content materials",
            "- Timber from sustainably managed forests", 
            "- Low embodied carbon options"
        ]
        return '\n'.join(materials)
    
    def _describe_waste_strategy(self, site: SiteInput) -> str:
        """Describe waste strategy"""
        return "Comprehensive waste management facilities are provided including recycling storage and collection arrangements."
    
    def _describe_habitat_creation(self, site: SiteInput) -> str:
        """Describe habitat creation"""
        return "New habitats will be created through native planting, wildlife-friendly landscaping, and green roof/wall systems where appropriate."
    
    def _describe_species_protection_measures(self, site: SiteInput) -> str:
        """Describe species protection measures"""
        return "Development will incorporate measures to protect and enhance opportunities for local wildlife including bird and bat boxes."
    
    def _describe_biodiversity_net_gain(self, site: SiteInput) -> str:
        """Describe biodiversity net gain"""
        return "The development will deliver measurable biodiversity net gain through habitat creation and enhancement measures."
    
    def _describe_climate_adaptation_measures(self, site: SiteInput) -> str:
        """Describe climate adaptation measures"""
        measures = [
            "- Flood resilient design and materials",
            "- Overheating prevention through orientation and shading",
            "- Drought resistant landscaping",
            "- Flexible design for future climate conditions"
        ]
        return '\n'.join(measures)
    
    def _describe_community_benefits(self, site: SiteInput) -> str:
        """Describe community benefits"""
        if site.development_type == 'RESIDENTIAL':
            return "- Additional housing to meet local needs\n- Affordable housing provision\n- Economic benefits during construction"
        return "- [Community benefits appropriate to development type]"
    
    def _describe_health_wellbeing_measures(self, site: SiteInput) -> str:
        """Describe health and wellbeing measures"""
        return "The development promotes health and wellbeing through active travel provision, access to green space, and high quality internal environments."
    
    def _summarise_design_achievements(self, site: SiteInput) -> str:
        """Summarise key design achievements"""
        achievements = [
            "- Contextually appropriate design responding to local character",
            "- High quality architecture and materials",
            "- Sustainable and energy efficient development",
            "- Fully accessible and inclusive design",
            "- Enhanced biodiversity and green infrastructure"
        ]
        return '\n'.join(achievements)
    
    def _summarise_community_benefits(self, site: SiteInput) -> str:
        """Summarise community benefits"""
        if site.development_type == 'RESIDENTIAL':
            benefits = [
                "- Additional housing contributing to local supply",
                "- High quality design enhancing local character",
                "- Economic benefits during construction phase"
            ]
        else:
            benefits = [
                "- High quality development enhancing local area",
                "- Economic benefits and potential employment",
                "- Enhanced public realm and accessibility"
            ]
        return '\n'.join(benefits)
    
    def _identify_image_requirements(self, context: Dict[str, Any]) -> List[str]:
        """Identify key images required for the statement"""
        
        images = [
            'Site location plan and aerial photograph',
            'Context analysis and character photographs', 
            'Design development sketches and options',
            'Final scheme plans, elevations and sections',
            'Materials palette and sample board',
            'Landscape design and planting plans',
            'Access and circulation diagrams',
            'Sustainability strategy diagrams'
        ]
        
        return images
    
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
async def generate_design_access_statement(
    site_input: SiteInput,
    constraints: List[Constraint],
    score: Score,
    recommendations: List[Recommendation],
    design_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive Design & Access Statement
    
    Main entry point for D&A statement generation
    """
    
    generator = DesignAccessStatementGenerator()
    return await generator.generate_design_access_statement(
        site_input, constraints, score, recommendations, design_data
    )