"""
Document Template Engine
Template management and content generation system
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class DocumentType(Enum):
    """Supported document types"""
    PLANNING_STATEMENT = "planning_statement"
    DESIGN_ACCESS_STATEMENT = "design_access_statement"
    HERITAGE_STATEMENT = "heritage_statement"
    TRANSPORT_STATEMENT = "transport_statement"
    ECOLOGY_STATEMENT = "ecology_statement"
    COVER_LETTER = "cover_letter"


class OutputFormat(Enum):
    """Supported output formats"""
    HTML = "html"
    MARKDOWN = "markdown"
    DOCX = "docx"
    PDF = "pdf"


@dataclass
class DocumentTemplate:
    """Template definition for document generation"""
    
    name: str
    document_type: DocumentType
    sections: List[str]
    required_fields: List[str]
    optional_fields: List[str]
    template_content: Dict[str, str]
    metadata: Dict[str, Any]
    
    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate that context contains required fields"""
        for field in self.required_fields:
            if field not in context:
                return False
        return True
    
    def get_missing_fields(self, context: Dict[str, Any]) -> List[str]:
        """Get list of missing required fields"""
        return [field for field in self.required_fields if field not in context]


class TemplateEngine:
    """Template processing and content generation engine"""
    
    def __init__(self):
        self.templates: Dict[str, DocumentTemplate] = {}
        self.output_formatters = {
            OutputFormat.HTML: self._format_html,
            OutputFormat.MARKDOWN: self._format_markdown,
            OutputFormat.DOCX: self._format_docx,
            OutputFormat.PDF: self._format_pdf
        }
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default document templates"""
        
        # Planning Statement Template
        planning_template = DocumentTemplate(
            name="Standard Planning Statement",
            document_type=DocumentType.PLANNING_STATEMENT,
            sections=[
                "executive_summary",
                "site_description", 
                "proposal_description",
                "planning_policy_context",
                "planning_assessment",
                "consultation_strategy",
                "conclusion"
            ],
            required_fields=[
                "site_input",
                "constraints",
                "score",
                "recommendations"
            ],
            optional_fields=[
                "custom_content",
                "images",
                "appendices"
            ],
            template_content={
                "header": self._get_planning_statement_header_template(),
                "footer": self._get_planning_statement_footer_template(),
                "section_styles": self._get_planning_statement_styles()
            },
            metadata={
                "version": "1.0",
                "created": datetime.utcnow().isoformat(),
                "description": "Standard template for planning statements"
            }
        )
        
        self.templates["planning_statement"] = planning_template
        
        # Design & Access Statement Template
        design_template = DocumentTemplate(
            name="Standard Design & Access Statement",
            document_type=DocumentType.DESIGN_ACCESS_STATEMENT,
            sections=[
                "introduction",
                "context_appraisal",
                "design_evolution",
                "design_principles", 
                "access_strategy",
                "sustainability",
                "conclusion"
            ],
            required_fields=[
                "site_input",
                "constraints",
                "score",
                "recommendations"
            ],
            optional_fields=[
                "design_data",
                "images",
                "appendices"
            ],
            template_content={
                "header": self._get_design_access_header_template(),
                "footer": self._get_design_access_footer_template(),
                "section_styles": self._get_design_access_styles()
            },
            metadata={
                "version": "1.0",
                "created": datetime.utcnow().isoformat(),
                "description": "Standard template for design and access statements"
            }
        )
        
        self.templates["design_access_statement"] = design_template
    
    def get_template(self, template_name: str) -> Optional[DocumentTemplate]:
        """Get template by name"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List available template names"""
        return list(self.templates.keys())
    
    def add_custom_template(self, template: DocumentTemplate):
        """Add a custom template"""
        self.templates[template.name] = template
    
    async def generate_document(
        self,
        template_name: str,
        content_sections: Dict[str, Dict[str, Any]],
        context: Dict[str, Any],
        output_format: OutputFormat = OutputFormat.HTML
    ) -> Dict[str, Any]:
        """
        Generate a complete document using specified template
        
        Args:
            template_name: Name of template to use
            content_sections: Generated content sections
            context: Context data for template processing
            output_format: Desired output format
            
        Returns:
            Dictionary containing formatted document and metadata
        """
        
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Validate context
        if not template.validate_context(context):
            missing_fields = template.get_missing_fields(context)
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Process template content
        processed_content = await self._process_template_content(
            template, content_sections, context
        )
        
        # Format output
        formatter = self.output_formatters.get(output_format)
        if not formatter:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        formatted_document = await formatter(template, processed_content, context)
        
        return {
            'document': formatted_document,
            'template_name': template_name,
            'output_format': output_format.value,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'template_version': template.metadata.get('version'),
                'word_count': self._calculate_word_count(processed_content),
                'section_count': len(content_sections)
            }
        }
    
    async def _process_template_content(
        self,
        template: DocumentTemplate,
        content_sections: Dict[str, Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process template content with context substitution"""
        
        processed_sections = {}
        
        # Process each section
        for section_name in template.sections:
            if section_name in content_sections:
                section_content = content_sections[section_name]
                processed_sections[section_name] = await self._process_section(
                    section_content, context, template
                )
            else:
                # Generate placeholder section
                processed_sections[section_name] = {
                    'title': section_name.replace('_', ' ').title(),
                    'content': f'[{section_name} content to be added]',
                    'placeholder': True
                }
        
        return {
            'sections': processed_sections,
            'header': await self._process_template_string(
                template.template_content.get('header', ''), context
            ),
            'footer': await self._process_template_string(
                template.template_content.get('footer', ''), context
            ),
            'styles': template.template_content.get('section_styles', {})
        }
    
    async def _process_section(
        self,
        section_content: Dict[str, Any],
        context: Dict[str, Any],
        template: DocumentTemplate
    ) -> Dict[str, Any]:
        """Process individual section content"""
        
        processed_section = {
            'title': section_content.get('title', ''),
            'content': section_content.get('content', ''),
            'image_refs': section_content.get('image_refs', []),
            'subsections': section_content.get('subsections', [])
        }
        
        # Process template variables in content
        if processed_section['content']:
            processed_section['content'] = await self._process_template_string(
                processed_section['content'], context
            )
        
        return processed_section
    
    async def _process_template_string(
        self,
        template_string: str,
        context: Dict[str, Any]
    ) -> str:
        """Process template string with variable substitution"""
        
        # Simple variable substitution using {{variable}} syntax
        def replace_variable(match):
            var_name = match.group(1).strip()
            return str(self._get_nested_value(context, var_name, f'{{{{{var_name}}}}}'))
        
        processed = re.sub(r'\{\{([^}]+)\}\}', replace_variable, template_string)
        
        return processed
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get nested value from dictionary using dot notation"""
        
        keys = key_path.split('.')
        value = data
        
        try:
            for key in keys:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except (AttributeError, KeyError, TypeError):
            return default
    
    async def _format_html(
        self,
        template: DocumentTemplate,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Format document as HTML"""
        
        html_parts = []
        
        # HTML document structure
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="en">')
        html_parts.append('<head>')
        html_parts.append('<meta charset="UTF-8">')
        html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append(f'<title>{self._get_document_title(context)}</title>')
        html_parts.append('<style>')
        html_parts.append(self._get_html_styles())
        html_parts.append('</style>')
        html_parts.append('</head>')
        html_parts.append('<body>')
        
        # Header
        if content.get('header'):
            html_parts.append('<header>')
            html_parts.append(self._markdown_to_html(content['header']))
            html_parts.append('</header>')
        
        # Main content
        html_parts.append('<main>')
        
        # Table of contents
        html_parts.append('<nav class="toc">')
        html_parts.append('<h2>Contents</h2>')
        html_parts.append('<ul>')
        for section_name, section in content['sections'].items():
            if not section.get('placeholder'):
                html_parts.append(f'<li><a href="#{section_name}">{section["title"]}</a></li>')
        html_parts.append('</ul>')
        html_parts.append('</nav>')
        
        # Document sections
        for section_name, section in content['sections'].items():
            if not section.get('placeholder'):
                html_parts.append(f'<section id="{section_name}">')
                html_parts.append(f'<h1>{section["title"]}</h1>')
                html_parts.append(self._markdown_to_html(section['content']))
                
                # Add image placeholders
                if section.get('image_refs'):
                    html_parts.append('<div class="images">')
                    for image_ref in section['image_refs']:
                        html_parts.append(f'<div class="image-placeholder">[{image_ref}]</div>')
                    html_parts.append('</div>')
                
                html_parts.append('</section>')
        
        html_parts.append('</main>')
        
        # Footer
        if content.get('footer'):
            html_parts.append('<footer>')
            html_parts.append(self._markdown_to_html(content['footer']))
            html_parts.append('</footer>')
        
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    async def _format_markdown(
        self,
        template: DocumentTemplate,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Format document as Markdown"""
        
        md_parts = []
        
        # Document header
        md_parts.append(f'# {self._get_document_title(context)}')
        md_parts.append('')
        
        if content.get('header'):
            md_parts.append(content['header'])
            md_parts.append('')
        
        # Table of contents
        md_parts.append('## Contents')
        md_parts.append('')
        for section_name, section in content['sections'].items():
            if not section.get('placeholder'):
                md_parts.append(f'- [{section["title"]}](#{section_name.replace("_", "-")})')
        md_parts.append('')
        
        # Document sections
        for section_name, section in content['sections'].items():
            if not section.get('placeholder'):
                md_parts.append(f'## {section["title"]} {{#{section_name.replace("_", "-")}}}')
                md_parts.append('')
                md_parts.append(section['content'])
                md_parts.append('')
                
                # Add image references
                if section.get('image_refs'):
                    md_parts.append('**Images:**')
                    for image_ref in section['image_refs']:
                        md_parts.append(f'- {image_ref}')
                    md_parts.append('')
        
        # Footer
        if content.get('footer'):
            md_parts.append('---')
            md_parts.append('')
            md_parts.append(content['footer'])
        
        return '\n'.join(md_parts)
    
    async def _format_docx(
        self,
        template: DocumentTemplate,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format document for DOCX generation"""
        
        # Return structured data that can be converted to DOCX
        # In production, would use python-docx library
        
        return {
            'format': 'docx',
            'title': self._get_document_title(context),
            'sections': [
                {
                    'title': section['title'],
                    'content': section['content'],
                    'level': 1,
                    'images': section.get('image_refs', [])
                }
                for section_name, section in content['sections'].items()
                if not section.get('placeholder')
            ],
            'styles': content.get('styles', {}),
            'metadata': {
                'author': 'Domus Planning AI',
                'subject': template.document_type.value,
                'created': datetime.utcnow().isoformat()
            }
        }
    
    async def _format_pdf(
        self,
        template: DocumentTemplate,
        content: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format document for PDF generation"""
        
        # Return structured data that can be converted to PDF
        # In production, would use reportlab or similar
        
        return {
            'format': 'pdf',
            'title': self._get_document_title(context),
            'sections': [
                {
                    'title': section['title'],
                    'content': section['content'],
                    'images': section.get('image_refs', [])
                }
                for section_name, section in content['sections'].items()
                if not section.get('placeholder')
            ],
            'styles': content.get('styles', {}),
            'page_settings': {
                'size': 'A4',
                'margins': {'top': 25, 'bottom': 25, 'left': 25, 'right': 25}
            }
        }
    
    def _get_document_title(self, context: Dict[str, Any]) -> str:
        """Generate document title from context"""
        
        site = context.get('site')
        if site and hasattr(site, 'address'):
            address = getattr(site, 'address', 'Unknown Address')
            return f'Planning Documentation: {address}'
        
        return 'Planning Documentation'
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert simple Markdown to HTML"""
        
        html = markdown_text
        
        # Headers
        html = re.sub(r'^### (.*$)', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*$)', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*$)', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Lists
        html = re.sub(r'^- (.*)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        html = html.replace('</li>\n<li>', '</li><li>')
        html = html.replace('</ul><ul>', '')
        
        # Paragraphs
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('<'):
                html_paragraphs.append(f'<p>{para}</p>')
            elif para:
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
    
    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML output"""
        
        return """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        
        header, footer {
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        footer {
            border-top: 2px solid #eee;
            border-bottom: none;
            padding-top: 20px;
            margin-top: 30px;
        }
        
        .toc {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            padding: 5px 0;
        }
        
        .toc a {
            text-decoration: none;
            color: #0066cc;
        }
        
        section {
            margin-bottom: 40px;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        
        h3 {
            color: #7f8c8d;
        }
        
        .images {
            margin: 20px 0;
        }
        
        .image-placeholder {
            background: #ecf0f1;
            border: 2px dashed #bdc3c7;
            padding: 20px;
            text-align: center;
            margin: 10px 0;
            color: #7f8c8d;
            font-style: italic;
        }
        
        ul {
            padding-left: 25px;
        }
        
        li {
            margin-bottom: 5px;
        }
        
        strong {
            color: #2c3e50;
        }
        """
    
    def _calculate_word_count(self, content: Dict[str, Any]) -> int:
        """Calculate word count for document content"""
        
        total_words = 0
        
        if 'sections' in content:
            for section in content['sections'].values():
                if 'content' in section and not section.get('placeholder'):
                    # Remove HTML/Markdown formatting for accurate count
                    text = re.sub(r'<[^>]+>', '', section['content'])
                    text = re.sub(r'\*+', '', text)
                    text = re.sub(r'#+', '', text)
                    words = text.split()
                    total_words += len(words)
        
        return total_words
    
    # Template content methods
    
    def _get_planning_statement_header_template(self) -> str:
        """Get header template for planning statements"""
        
        return """
        **Planning Statement**
        
        **Site:** {{site.address}}  
        **Reference:** {{site.reference}}  
        **Date:** {{generation_date}}  
        
        **Prepared by:** Domus Planning AI  
        **On behalf of:** {{site.applicant_details.name}}
        """
    
    def _get_planning_statement_footer_template(self) -> str:
        """Get footer template for planning statements"""
        
        return """
        ---
        
        This Planning Statement has been prepared using AI-powered planning analysis.  
        Generated by Domus Planning AI on {{generation_date}}.
        
        **Disclaimer:** This document should be reviewed by a qualified planning professional 
        before submission to the Local Planning Authority.
        """
    
    def _get_planning_statement_styles(self) -> Dict[str, str]:
        """Get styles for planning statement sections"""
        
        return {
            'executive_summary': 'summary',
            'conclusion': 'conclusion',
            'planning_assessment': 'assessment'
        }
    
    def _get_design_access_header_template(self) -> str:
        """Get header template for design & access statements"""
        
        return """
        **Design & Access Statement**
        
        **Development:** {{site.proposal_description}}  
        **Site:** {{site.address}}  
        **Reference:** {{site.reference}}  
        **Date:** {{generation_date}}  
        
        **Prepared by:** Domus Planning AI  
        **On behalf of:** {{site.applicant_details.name}}
        """
    
    def _get_design_access_footer_template(self) -> str:
        """Get footer template for design & access statements"""
        
        return """
        ---
        
        This Design & Access Statement has been prepared using AI-powered design analysis.  
        Generated by Domus Planning AI on {{generation_date}}.
        
        **Note:** All images and technical drawings should be prepared by qualified professionals 
        and reviewed before submission.
        """
    
    def _get_design_access_styles(self) -> Dict[str, str]:
        """Get styles for design & access statement sections"""
        
        return {
            'context_appraisal': 'analysis',
            'design_principles': 'principles',
            'access_strategy': 'strategy'
        }


# Singleton template engine instance
template_engine = TemplateEngine()


# Convenience functions
async def generate_document_from_template(
    template_name: str,
    content_sections: Dict[str, Dict[str, Any]],
    context: Dict[str, Any],
    output_format: OutputFormat = OutputFormat.HTML
) -> Dict[str, Any]:
    """Generate document using template engine"""
    
    return await template_engine.generate_document(
        template_name, content_sections, context, output_format
    )


def get_available_templates() -> List[str]:
    """Get list of available templates"""
    
    return template_engine.list_templates()


def get_template_info(template_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific template"""
    
    template = template_engine.get_template(template_name)
    if not template:
        return None
    
    return {
        'name': template.name,
        'document_type': template.document_type.value,
        'sections': template.sections,
        'required_fields': template.required_fields,
        'optional_fields': template.optional_fields,
        'metadata': template.metadata
    }