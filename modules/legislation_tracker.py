"""
Legislation Tracker - Forward-Looking Planning Law Monitor
Tracks NPPF, NPPG, and planning law changes with impact analysis on projects
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta, date
import logging
import hashlib
import json
import re
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class LegislationType(Enum):
    """Types of planning legislation"""
    NPPF = "nppf"  # National Planning Policy Framework
    NPPG = "nppg"  # Planning Practice Guidance
    LOCAL_PLAN = "local_plan"
    PLANNING_ACT = "planning_act"
    STATUTORY_INSTRUMENT = "statutory_instrument"
    CIRCULAR = "circular"
    CASE_LAW = "case_law"
    COUNCIL_POLICY = "council_policy"

class ChangeType(Enum):
    """Types of legislation changes"""
    NEW_DOCUMENT = "new_document"
    MAJOR_REVISION = "major_revision"
    MINOR_UPDATE = "minor_update"
    SECTION_ADDED = "section_added"
    SECTION_REMOVED = "section_removed"
    PARAGRAPH_CHANGED = "paragraph_changed"
    CONSULTATION = "consultation"
    APPEAL_DECISION = "appeal_decision"

class ImpactLevel(Enum):
    """Impact level on development projects"""
    CRITICAL = "critical"  # Stops development
    HIGH = "high"  # Major changes required
    MEDIUM = "medium"  # Some adjustments needed
    LOW = "low"  # Minor considerations
    NONE = "none"  # No impact

@dataclass
class LegislationSource:
    """Configuration for legislation sources"""
    name: str
    type: LegislationType
    url: str
    selector: str  # CSS selector for content
    update_frequency: str  # daily, weekly, monthly
    last_check: Optional[datetime] = None
    is_active: bool = True
    authority: str = "government"  # government, council, court

@dataclass
class LegislationChange:
    """A detected change in planning legislation"""
    change_id: str
    source_name: str
    legislation_type: LegislationType
    change_type: ChangeType
    title: str
    description: str
    content_hash: str
    url: str
    effective_date: Optional[date] = None
    consultation_deadline: Optional[date] = None
    detected_date: datetime = None
    keywords: List[str] = None
    affected_topics: List[str] = None
    full_content: str = ""
    
    def __post_init__(self):
        if self.detected_date is None:
            self.detected_date = datetime.now()
        if self.keywords is None:
            self.keywords = []
        if self.affected_topics is None:
            self.affected_topics = []

@dataclass 
class ProjectImpactAssessment:
    """Assessment of how legislation change impacts a specific project"""
    project_id: str
    change_id: str
    impact_level: ImpactLevel
    impact_description: str
    affected_aspects: List[str]  # e.g., ["density", "affordable_housing", "design"]
    required_actions: List[str]
    compliance_risk: float  # 0-100 risk score
    urgency_score: float  # 0-100 urgency score
    estimated_cost_impact: Optional[float] = None
    estimated_time_impact: Optional[int] = None  # Days
    mitigation_strategies: List[str] = None
    
    def __post_init__(self):
        if self.mitigation_strategies is None:
            self.mitigation_strategies = []

@dataclass
class TrackerAlert:
    """Alert generated for important changes"""
    alert_id: str
    change_id: str
    alert_type: str  # urgent, important, informational
    message: str
    affected_projects: List[str]
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

class LegislationScraper:
    """Scrapes legislation sources for changes"""
    
    def __init__(self):
        self.sources = self._get_default_sources()
        self.session = None  # Would be requests session
        
    def _get_default_sources(self) -> List[LegislationSource]:
        """Get default legislation sources to monitor"""
        return [
            LegislationSource(
                name="NPPF",
                type=LegislationType.NPPF,
                url="https://www.gov.uk/government/publications/national-planning-policy-framework--2",
                selector=".gem-c-govspeak",
                update_frequency="weekly"
            ),
            LegislationSource(
                name="NPPG",
                type=LegislationType.NPPG,
                url="https://www.gov.uk/government/collections/planning-practice-guidance",
                selector=".gem-c-govspeak",
                update_frequency="weekly"
            ),
            LegislationSource(
                name="Planning Portal Updates",
                type=LegislationType.PLANNING_ACT,
                url="https://www.planningportal.co.uk/info/200125/do_you_need_permission/9/permitted_development_rights",
                selector=".main-content",
                update_frequency="weekly"
            ),
            LegislationSource(
                name="Planning Inspectorate Appeals",
                type=LegislationType.CASE_LAW,
                url="https://acp.planninginspectorate.gov.uk/",
                selector=".case-summary",
                update_frequency="daily"
            )
        ]
    
    def check_source_for_changes(self, source: LegislationSource) -> List[LegislationChange]:
        """Check a single source for changes"""
        logger.info(f"Checking {source.name} for changes")
        
        changes = []
        
        try:
            # This would implement actual web scraping
            # For now, simulate detection of changes
            
            # Calculate content hash (would be from actual scraping)
            dummy_content = f"Content from {source.name} at {datetime.now()}"
            content_hash = hashlib.md5(dummy_content.encode()).hexdigest()
            
            # Check if content has changed (would compare with stored hash)
            has_changed = True  # Simulate change detection
            
            if has_changed:
                change = LegislationChange(
                    change_id=f"{source.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    source_name=source.name,
                    legislation_type=source.type,
                    change_type=ChangeType.MINOR_UPDATE,
                    title=f"Update to {source.name}",
                    description=f"Detected changes in {source.name}",
                    content_hash=content_hash,
                    url=source.url,
                    full_content=dummy_content
                )
                
                # Extract keywords and topics
                change.keywords = self._extract_keywords(change.full_content)
                change.affected_topics = self._extract_topics(change.full_content)
                
                changes.append(change)
            
            # Update last check time
            source.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking {source.name}: {e}")
        
        return changes
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        planning_keywords = [
            "affordable housing", "density", "height", "design", "heritage",
            "conservation", "flood risk", "biodiversity", "net gain",
            "climate change", "transport", "infrastructure", "viability",
            "section 106", "cil", "permitted development", "prior approval",
            "outline permission", "reserved matters", "conditions",
            "enforcement", "appeal", "inquiry", "examination"
        ]
        
        found_keywords = []
        content_lower = content.lower()
        
        for keyword in planning_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract affected planning topics"""
        topic_patterns = {
            "housing": r"(housing|residential|dwelling|home)",
            "design": r"(design|appearance|character|architecture)",
            "environment": r"(environment|ecology|biodiversity|climate)",
            "transport": r"(transport|traffic|parking|highway)",
            "heritage": r"(heritage|conservation|listed|historic)",
            "flooding": r"(flood|drainage|sustainable|suds)",
            "economy": r"(employment|commercial|retail|economic)"
        }
        
        topics = []
        content_lower = content.lower()
        
        for topic, pattern in topic_patterns.items():
            if re.search(pattern, content_lower):
                topics.append(topic)
        
        return topics

class ImpactAnalyser:
    """Analyses impact of legislation changes on projects"""
    
    def __init__(self):
        self.impact_rules = self._get_impact_rules()
    
    def _get_impact_rules(self) -> Dict[str, Dict]:
        """Get rules for assessing impact of changes"""
        return {
            "affordable_housing": {
                "keywords": ["affordable housing", "social rent", "shared ownership"],
                "project_aspects": ["unit_mix", "viability", "planning_obligations"],
                "base_impact": ImpactLevel.HIGH
            },
            "density": {
                "keywords": ["density", "dwellings per hectare", "unit count"],
                "project_aspects": ["scheme_design", "viability", "planning_strategy"],
                "base_impact": ImpactLevel.HIGH
            },
            "design": {
                "keywords": ["design", "appearance", "character", "materials"],
                "project_aspects": ["design", "planning_strategy"],
                "base_impact": ImpactLevel.MEDIUM
            },
            "heritage": {
                "keywords": ["heritage", "conservation", "listed building"],
                "project_aspects": ["design", "planning_strategy", "constraints"],
                "base_impact": ImpactLevel.HIGH
            },
            "biodiversity": {
                "keywords": ["biodiversity", "net gain", "ecology", "habitat"],
                "project_aspects": ["environmental", "planning_obligations", "constraints"],
                "base_impact": ImpactLevel.MEDIUM
            },
            "permitted_development": {
                "keywords": ["permitted development", "prior approval", "pdr"],
                "project_aspects": ["planning_strategy", "scheme_design"],
                "base_impact": ImpactLevel.MEDIUM
            }
        }
    
    def assess_project_impact(self, change: LegislationChange, project_data: Dict[str, Any]) -> ProjectImpactAssessment:
        """Assess impact of a change on a specific project"""
        
        project_id = project_data.get("id", "unknown")
        
        # Initialize assessment
        assessment = ProjectImpactAssessment(
            project_id=project_id,
            change_id=change.change_id,
            impact_level=ImpactLevel.NONE,
            impact_description="No significant impact identified",
            affected_aspects=[],
            required_actions=[],
            compliance_risk=0,
            urgency_score=0
        )
        
        # Check for keyword matches
        relevant_rules = []
        for rule_name, rule in self.impact_rules.items():
            if any(keyword in change.keywords for keyword in rule["keywords"]):
                relevant_rules.append((rule_name, rule))
        
        if not relevant_rules:
            return assessment
        
        # Calculate impact level
        max_impact = ImpactLevel.NONE
        affected_aspects = []
        
        for rule_name, rule in relevant_rules:
            if rule["base_impact"].value == "critical":
                max_impact = ImpactLevel.CRITICAL
            elif rule["base_impact"].value == "high" and max_impact.value not in ["critical"]:
                max_impact = ImpactLevel.HIGH
            elif rule["base_impact"].value == "medium" and max_impact.value not in ["critical", "high"]:
                max_impact = ImpactLevel.MEDIUM
            elif max_impact.value == "none":
                max_impact = ImpactLevel.LOW
            
            affected_aspects.extend(rule["project_aspects"])
        
        assessment.impact_level = max_impact
        assessment.affected_aspects = list(set(affected_aspects))
        
        # Generate impact description
        assessment.impact_description = self._generate_impact_description(change, relevant_rules, project_data)
        
        # Generate required actions
        assessment.required_actions = self._generate_required_actions(change, relevant_rules, project_data)
        
        # Calculate risk and urgency scores
        assessment.compliance_risk = self._calculate_compliance_risk(change, assessment.impact_level, project_data)
        assessment.urgency_score = self._calculate_urgency_score(change, assessment.impact_level)
        
        # Estimate cost and time impacts
        assessment.estimated_cost_impact = self._estimate_cost_impact(assessment.impact_level, project_data)
        assessment.estimated_time_impact = self._estimate_time_impact(assessment.impact_level)
        
        # Generate mitigation strategies
        assessment.mitigation_strategies = self._generate_mitigation_strategies(change, assessment)
        
        return assessment
    
    def _generate_impact_description(self, change: LegislationChange, rules: List[Tuple], project_data: Dict) -> str:
        """Generate human-readable impact description"""
        rule_names = [rule[0] for rule in rules]
        
        if "affordable_housing" in rule_names:
            return f"Changes to affordable housing requirements may affect your unit mix and viability calculations"
        elif "density" in rule_names:
            return f"Density policy changes may impact your proposed scheme scale and planning strategy"
        elif "design" in rule_names:
            return f"New design requirements may require updates to your design approach and materials"
        elif "heritage" in rule_names:
            return f"Heritage policy changes may affect development approach in sensitive areas"
        else:
            return f"Planning policy updates may require review of your planning strategy and compliance approach"
    
    def _generate_required_actions(self, change: LegislationChange, rules: List[Tuple], project_data: Dict) -> List[str]:
        """Generate list of required actions"""
        actions = []
        rule_names = [rule[0] for rule in rules]
        
        if "affordable_housing" in rule_names:
            actions.extend([
                "Review affordable housing requirements",
                "Update unit mix if necessary", 
                "Recalculate financial viability",
                "Check Section 106 implications"
            ])
        
        if "density" in rule_names:
            actions.extend([
                "Review density calculations",
                "Check compliance with new thresholds",
                "Consider scheme redesign if required"
            ])
        
        if "design" in rule_names:
            actions.extend([
                "Review design policies",
                "Update Design and Access Statement",
                "Consider design revisions"
            ])
        
        # Add general actions
        actions.extend([
            "Review planning statement for policy references",
            "Consider legal advice if major changes required",
            "Update risk register"
        ])
        
        return list(set(actions))  # Remove duplicates
    
    def _calculate_compliance_risk(self, change: LegislationChange, impact_level: ImpactLevel, project_data: Dict) -> float:
        """Calculate compliance risk score 0-100"""
        base_risk = {
            ImpactLevel.CRITICAL: 90,
            ImpactLevel.HIGH: 70,
            ImpactLevel.MEDIUM: 40,
            ImpactLevel.LOW: 20,
            ImpactLevel.NONE: 0
        }
        
        risk = base_risk[impact_level]
        
        # Adjust based on project stage
        project_stage = project_data.get("stage", "pre-application")
        if project_stage in ["submitted", "determination"]:
            risk += 20  # Higher risk if already submitted
        elif project_stage == "appeal":
            risk += 30  # Very high risk at appeal
        
        return min(100, risk)
    
    def _calculate_urgency_score(self, change: LegislationChange, impact_level: ImpactLevel) -> float:
        """Calculate urgency score 0-100"""
        base_urgency = {
            ImpactLevel.CRITICAL: 95,
            ImpactLevel.HIGH: 75,
            ImpactLevel.MEDIUM: 50,
            ImpactLevel.LOW: 25,
            ImpactLevel.NONE: 0
        }
        
        urgency = base_urgency[impact_level]
        
        # Adjust based on effective date
        if change.effective_date:
            days_until_effective = (change.effective_date - date.today()).days
            if days_until_effective <= 30:
                urgency += 20
            elif days_until_effective <= 90:
                urgency += 10
        
        # Adjust based on consultation deadline
        if change.consultation_deadline:
            days_until_deadline = (change.consultation_deadline - date.today()).days
            if days_until_deadline <= 14:
                urgency += 30
            elif days_until_deadline <= 30:
                urgency += 15
        
        return min(100, urgency)
    
    def _estimate_cost_impact(self, impact_level: ImpactLevel, project_data: Dict) -> Optional[float]:
        """Estimate financial impact"""
        if impact_level == ImpactLevel.NONE:
            return 0
        
        project_value = project_data.get("estimated_value", 1000000)
        
        impact_percentages = {
            ImpactLevel.CRITICAL: 0.15,  # 15% of project value
            ImpactLevel.HIGH: 0.08,     # 8% of project value
            ImpactLevel.MEDIUM: 0.03,   # 3% of project value
            ImpactLevel.LOW: 0.01       # 1% of project value
        }
        
        return project_value * impact_percentages.get(impact_level, 0)
    
    def _estimate_time_impact(self, impact_level: ImpactLevel) -> Optional[int]:
        """Estimate time impact in days"""
        time_impacts = {
            ImpactLevel.CRITICAL: 120,  # 4 months
            ImpactLevel.HIGH: 60,       # 2 months
            ImpactLevel.MEDIUM: 30,     # 1 month
            ImpactLevel.LOW: 14,        # 2 weeks
            ImpactLevel.NONE: 0
        }
        
        return time_impacts.get(impact_level, 0)
    
    def _generate_mitigation_strategies(self, change: LegislationChange, assessment: ProjectImpactAssessment) -> List[str]:
        """Generate mitigation strategies"""
        strategies = []
        
        if assessment.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            strategies.extend([
                "Engage planning consultant immediately",
                "Consider pre-application advice meeting",
                "Review similar recent applications",
                "Prepare alternative scheme options"
            ])
        
        if assessment.impact_level == ImpactLevel.MEDIUM:
            strategies.extend([
                "Monitor for further guidance",
                "Update planning strategy",
                "Consider stakeholder engagement"
            ])
        
        if "affordable_housing" in assessment.affected_aspects:
            strategies.append("Engage with affordable housing specialist")
        
        if "design" in assessment.affected_aspects:
            strategies.append("Engage with design team to review proposals")
        
        return strategies

class LegislationTracker:
    """Main legislation tracking system"""
    
    def __init__(self):
        self.scraper = LegislationScraper()
        self.analyser = ImpactAnalyser()
        self.changes_db = []  # Would be database
        self.alerts_db = []   # Would be database
        
    def run_daily_check(self) -> Dict[str, Any]:
        """Run daily legislation monitoring"""
        logger.info("Starting daily legislation check")
        
        new_changes = []
        alerts = []
        
        # Check all active sources
        for source in self.scraper.sources:
            if source.is_active and self._should_check_source(source):
                source_changes = self.scraper.check_source_for_changes(source)
                new_changes.extend(source_changes)
        
        # Store new changes
        for change in new_changes:
            self.changes_db.append(change)
        
        # Generate alerts for significant changes
        for change in new_changes:
            if self._is_significant_change(change):
                alert = self._create_alert(change)
                alerts.append(alert)
                self.alerts_db.append(alert)
        
        result = {
            "check_date": datetime.now(),
            "sources_checked": len([s for s in self.scraper.sources if s.is_active]),
            "new_changes": len(new_changes),
            "new_alerts": len(alerts),
            "changes": [asdict(c) for c in new_changes],
            "alerts": [asdict(a) for a in alerts]
        }
        
        logger.info(f"Daily check complete: {len(new_changes)} changes, {len(alerts)} alerts")
        
        return result
    
    def assess_project_impacts(self, project_data: Dict[str, Any], 
                             days_lookback: int = 30) -> List[ProjectImpactAssessment]:
        """Assess impacts of recent changes on a project"""
        
        project_id = project_data.get("id", "unknown")
        logger.info(f"Assessing legislation impacts for project {project_id}")
        
        # Get recent changes
        cutoff_date = datetime.now() - timedelta(days=days_lookback)
        recent_changes = [c for c in self.changes_db if c.detected_date >= cutoff_date]
        
        # Assess impact of each change
        assessments = []
        for change in recent_changes:
            assessment = self.analyser.assess_project_impact(change, project_data)
            if assessment.impact_level != ImpactLevel.NONE:
                assessments.append(assessment)
        
        # Sort by urgency score
        assessments.sort(key=lambda a: a.urgency_score, reverse=True)
        
        logger.info(f"Found {len(assessments)} impactful changes for project {project_id}")
        
        return assessments
    
    def get_impact_summary(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of legislation impacts for a project"""
        
        assessments = self.assess_project_impacts(project_data)
        
        if not assessments:
            return {
                "project_id": project_data.get("id"),
                "total_impacts": 0,
                "risk_level": "low",
                "summary": "No significant legislation impacts identified",
                "next_review_date": (datetime.now() + timedelta(days=7)).date()
            }
        
        # Calculate overall risk
        max_risk = max(a.compliance_risk for a in assessments)
        high_urgency_count = len([a for a in assessments if a.urgency_score >= 70])
        
        if max_risk >= 80 or high_urgency_count >= 2:
            risk_level = "high"
        elif max_risk >= 50 or high_urgency_count >= 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Generate summary
        critical_count = len([a for a in assessments if a.impact_level == ImpactLevel.CRITICAL])
        high_count = len([a for a in assessments if a.impact_level == ImpactLevel.HIGH])
        
        if critical_count > 0:
            summary = f"{critical_count} critical and {high_count} high impact changes require immediate attention"
        elif high_count > 0:
            summary = f"{high_count} high impact changes require review and action"
        else:
            summary = f"{len(assessments)} moderate impact changes identified for monitoring"
        
        return {
            "project_id": project_data.get("id"),
            "total_impacts": len(assessments),
            "risk_level": risk_level,
            "max_compliance_risk": max_risk,
            "high_urgency_count": high_urgency_count,
            "summary": summary,
            "top_impacts": [asdict(a) for a in assessments[:5]],
            "next_review_date": (datetime.now() + timedelta(days=7)).date()
        }
    
    def _should_check_source(self, source: LegislationSource) -> bool:
        """Check if source should be checked based on frequency"""
        if not source.last_check:
            return True
        
        frequency_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }
        
        days_since_check = (datetime.now() - source.last_check).days
        required_interval = frequency_days.get(source.update_frequency, 7)
        
        return days_since_check >= required_interval
    
    def _is_significant_change(self, change: LegislationChange) -> bool:
        """Check if change is significant enough to generate alert"""
        significant_keywords = [
            "affordable housing", "density", "permitted development",
            "heritage", "conservation", "climate change", "biodiversity"
        ]
        
        return any(keyword in change.keywords for keyword in significant_keywords)
    
    def _create_alert(self, change: LegislationChange) -> TrackerAlert:
        """Create alert for significant change"""
        alert_type = "important"
        
        if change.change_type in [ChangeType.MAJOR_REVISION, ChangeType.NEW_DOCUMENT]:
            alert_type = "urgent"
        
        return TrackerAlert(
            alert_id=f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            change_id=change.change_id,
            alert_type=alert_type,
            message=f"New {change.legislation_type.value.upper()} change: {change.title}",
            affected_projects=[],  # Would be populated based on project analysis
            created_at=datetime.now()
        )
    
    def export_impact_report(self, project_data: Dict[str, Any]) -> bytes:
        """Export detailed impact report"""
        # This would generate PDF/Excel report
        return b"Impact report would be generated here"

# Helper functions
def create_sample_project_data() -> Dict[str, Any]:
    """Create sample project data for testing"""
    return {
        "id": "PROJ_001",
        "name": "Sample Residential Development",
        "location": "Test Town",
        "stage": "pre-application",
        "estimated_value": 2500000,
        "unit_count": 15,
        "building_type": "houses",
        "site_area": 0.8,
        "affordable_housing_required": True,
        "conservation_area": False,
        "flood_zone": "1"
    }

# Global tracker instance
legislation_tracker = LegislationTracker()

# Export classes and functions
__all__ = [
    "LegislationType",
    "ChangeType",
    "ImpactLevel",
    "LegislationSource",
    "LegislationChange",
    "ProjectImpactAssessment",
    "TrackerAlert",
    "LegislationScraper",
    "ImpactAnalyser",
    "LegislationTracker",
    "legislation_tracker",
    "create_sample_project_data"
]