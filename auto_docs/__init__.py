"""
Auto-Generated Planning Documents Package
AI-powered document generation for Planning Applications
"""

from .planning_statement import generate_planning_statement
from .design_access import generate_design_access_statement
from .templates import DocumentTemplate, TemplateEngine
from .generators import DocumentGenerator

__version__ = "1.0.0"
__all__ = [
    "generate_planning_statement",
    "generate_design_access_statement", 
    "DocumentTemplate",
    "TemplateEngine",
    "DocumentGenerator"
]