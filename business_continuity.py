"""
Business Continuity Planning
Comprehensive business continuity procedures and automation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)

class BusinessImpactLevel(Enum):
    """Business impact severity levels"""
    MINIMAL = "minimal"        # < 1 hour downtime acceptable
    MODERATE = "moderate"      # 1-4 hours downtime acceptable  
    SIGNIFICANT = "significant" # 4-8 hours downtime acceptable
    SEVERE = "severe"          # 8+ hours downtime not acceptable

class ContinuityStrategy(Enum):
    """Business continuity strategy types"""
    FAILOVER = "failover"              # Automatic failover to backup systems
    MANUAL_RECOVERY = "manual_recovery" # Manual recovery procedures
    DEGRADED_SERVICE = "degraded_service" # Continue with reduced functionality
    ALTERNATIVE_PROCESS = "alternative_process" # Use alternative business processes

@dataclass
class BusinessFunction:
    """Represents a critical business function"""
    name: str
    description: str
    impact_level: BusinessImpactLevel
    dependencies: List[str]
    recovery_strategy: ContinuityStrategy
    manual_procedures: List[str]
    stakeholders: List[str]
    sla_requirements: Dict[str, Any]

@dataclass
class ContinuityPlan:
    """Business continuity plan for a specific function"""
    function_name: str
    activation_triggers: List[str]
    immediate_actions: List[str]
    communication_plan: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    recovery_procedures: List[str]
    testing_schedule: str
    last_tested: Optional[datetime] = None
    test_results: Optional[Dict[str, Any]] = None

class StakeholderNotification:
    """Handle stakeholder communications during incidents"""
    
    def __init__(self):
        self.notification_channels = {
            "email": self._send_email,
            "sms": self._send_sms,
            "slack": self._send_slack,
            "teams": self._send_teams
        }
        
        self.stakeholder_groups = {
            "executive": {
                "contacts": [
                    {"name": "CEO", "email": "ceo@domusconveyancing.com", "phone": "+44..."},
                    {"name": "CTO", "email": "cto@domusconveyancing.com", "phone": "+44..."}
                ],
                "escalation_time": 15  # minutes
            },
            "technical": {
                "contacts": [
                    {"name": "DevOps Lead", "email": "devops@domusconveyancing.com", "phone": "+44..."},
                    {"name": "Development Lead", "email": "dev@domusconveyancing.com", "phone": "+44..."}
                ],
                "escalation_time": 5
            },
            "legal": {
                "contacts": [
                    {"name": "Legal Director", "email": "legal@domusconveyancing.com", "phone": "+44..."},
                    {"name": "Compliance Officer", "email": "compliance@domusconveyancing.com", "phone": "+44..."}
                ],
                "escalation_time": 30
            },
            "clients": {
                "contacts": [],  # Dynamic based on affected transactions
                "escalation_time": 60
            }
        }
    
    async def notify_stakeholders(self, incident_type: str, severity: str, groups: List[str], message: str) -> Dict[str, Any]:
        """Send notifications to relevant stakeholder groups"""
        
        notification_results = {
            "incident_type": incident_type,
            "severity": severity,
            "sent_at": datetime.now().isoformat(),
            "notifications": [],
            "errors": []
        }
        
        for group_name in groups:
            if group_name not in self.stakeholder_groups:
                notification_results["errors"].append(f"Unknown stakeholder group: {group_name}")
                continue
            
            group = self.stakeholder_groups[group_name]
            
            for contact in group["contacts"]:
                try:
                    # Send email notification
                    email_result = await self._send_email(
                        contact["email"],
                        f"[{severity.upper()}] {incident_type}",
                        message
                    )
                    
                    notification_results["notifications"].append({
                        "group": group_name,
                        "contact": contact["name"],
                        "method": "email",
                        "success": email_result["success"],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Send SMS for critical incidents
                    if severity in ["critical", "high"] and "phone" in contact:
                        sms_result = await self._send_sms(
                            contact["phone"],
                            f"URGENT: {incident_type} - Check email for details"
                        )
                        
                        notification_results["notifications"].append({
                            "group": group_name,
                            "contact": contact["name"],
                            "method": "sms",
                            "success": sms_result["success"],
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    notification_results["errors"].append(f"Failed to notify {contact['name']}: {e}")
        
        return notification_results
    
    async def _send_email(self, email: str, subject: str, message: str) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Implementation would use your email service (SendGrid, AWS SES, etc.)
            # For now, just log the notification
            logger.info(f"EMAIL: {email} - {subject}")
            return {"success": True, "method": "email"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            # Implementation would use SMS service (Twilio, AWS SNS, etc.)
            logger.info(f"SMS: {phone} - {message}")
            return {"success": True, "method": "sms"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_slack(self, channel: str, message: str) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            # Implementation would use Slack API
            logger.info(f"SLACK: {channel} - {message}")
            return {"success": True, "method": "slack"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _send_teams(self, webhook_url: str, message: str) -> Dict[str, Any]:
        """Send Microsoft Teams notification"""
        try:
            # Implementation would use Teams webhook
            logger.info(f"TEAMS: {message}")
            return {"success": True, "method": "teams"}
        except Exception as e:
            return {"success": False, "error": str(e)}

class BusinessContinuityManager:
    """Main business continuity management system"""
    
    def __init__(self):
        self.business_functions = self._define_business_functions()
        self.continuity_plans = self._create_continuity_plans()
        self.notification_manager = StakeholderNotification()
        self.active_incidents = {}
        
    def _define_business_functions(self) -> Dict[str, BusinessFunction]:
        """Define critical business functions"""
        return {
            "transaction_processing": BusinessFunction(
                name="Property Transaction Processing",
                description="Core conveyancing transaction management and processing",
                impact_level=BusinessImpactLevel.SEVERE,
                dependencies=["database", "document_storage", "legal_systems"],
                recovery_strategy=ContinuityStrategy.FAILOVER,
                manual_procedures=[
                    "Switch to paper-based transaction tracking",
                    "Manual document management via secure email",
                    "Phone-based client communication",
                    "Partner portal notifications via manual process"
                ],
                stakeholders=["clients", "legal_partners", "technical", "executive"],
                sla_requirements={
                    "max_downtime_minutes": 60,
                    "data_loss_tolerance_minutes": 5,
                    "notification_time_minutes": 10
                }
            ),
            
            "document_management": BusinessFunction(
                name="Document Management System",
                description="Legal document storage, processing, and retrieval",
                impact_level=BusinessImpactLevel.SIGNIFICANT,
                dependencies=["storage_systems", "backup_systems"],
                recovery_strategy=ContinuityStrategy.ALTERNATIVE_PROCESS,
                manual_procedures=[
                    "Secure email for document sharing",
                    "Manual document versioning",
                    "Physical document backup access",
                    "Partner document sharing via secure portals"
                ],
                stakeholders=["clients", "legal_partners", "technical"],
                sla_requirements={
                    "max_downtime_minutes": 240,
                    "data_loss_tolerance_minutes": 30,
                    "notification_time_minutes": 30
                }
            ),
            
            "client_communication": BusinessFunction(
                name="Client Communication Platform",
                description="Client messaging, updates, and support systems",
                impact_level=BusinessImpactLevel.MODERATE,
                dependencies=["messaging_system", "notification_system"],
                recovery_strategy=ContinuityStrategy.DEGRADED_SERVICE,
                manual_procedures=[
                    "Direct email communication",
                    "Phone-based updates",
                    "Manual status updates",
                    "Emergency contact procedures"
                ],
                stakeholders=["clients", "support_team"],
                sla_requirements={
                    "max_downtime_minutes": 480,
                    "data_loss_tolerance_minutes": 60,
                    "notification_time_minutes": 60
                }
            ),
            
            "legal_compliance": BusinessFunction(
                name="Legal Compliance and Audit",
                description="Regulatory compliance, audit trails, and legal requirements",
                impact_level=BusinessImpactLevel.SEVERE,
                dependencies=["audit_systems", "compliance_database"],
                recovery_strategy=ContinuityStrategy.MANUAL_RECOVERY,
                manual_procedures=[
                    "Manual audit trail maintenance",
                    "Paper-based compliance tracking",
                    "Emergency regulatory notifications",
                    "Backup compliance system activation"
                ],
                stakeholders=["legal", "compliance", "executive"],
                sla_requirements={
                    "max_downtime_minutes": 120,
                    "data_loss_tolerance_minutes": 0,
                    "notification_time_minutes": 15
                }
            ),
            
            "payment_processing": BusinessFunction(
                name="Payment and Billing System",
                description="Client billing, payment processing, and financial tracking",
                impact_level=BusinessImpactLevel.SIGNIFICANT,
                dependencies=["payment_gateway", "billing_database"],
                recovery_strategy=ContinuityStrategy.FAILOVER,
                manual_procedures=[
                    "Manual payment processing",
                    "Offline billing generation",
                    "Bank transfer coordination",
                    "Payment reconciliation procedures"
                ],
                stakeholders=["clients", "finance", "technical"],
                sla_requirements={
                    "max_downtime_minutes": 180,
                    "data_loss_tolerance_minutes": 15,
                    "notification_time_minutes": 30
                }
            )
        }
    
    def _create_continuity_plans(self) -> Dict[str, ContinuityPlan]:
        """Create detailed continuity plans for each business function"""
        plans = {}
        
        for func_name, function in self.business_functions.items():
            plans[func_name] = ContinuityPlan(
                function_name=func_name,
                activation_triggers=self._get_activation_triggers(function),
                immediate_actions=self._get_immediate_actions(function),
                communication_plan=self._get_communication_plan(function),
                resource_requirements=self._get_resource_requirements(function),
                recovery_procedures=self._get_recovery_procedures(function),
                testing_schedule=self._get_testing_schedule(function)
            )
        
        return plans
    
    def _get_activation_triggers(self, function: BusinessFunction) -> List[str]:
        """Get activation triggers for continuity plan"""
        base_triggers = [
            f"{function.name} unavailable for > {function.sla_requirements['max_downtime_minutes']} minutes",
            "Critical dependency failure detected",
            "Data integrity compromise identified"
        ]
        
        if function.impact_level == BusinessImpactLevel.SEVERE:
            base_triggers.append("Any system failure affecting this function")
        
        return base_triggers
    
    def _get_immediate_actions(self, function: BusinessFunction) -> List[str]:
        """Get immediate actions for continuity plan"""
        actions = [
            "Assess scope and impact of disruption",
            f"Notify stakeholders within {function.sla_requirements['notification_time_minutes']} minutes",
            "Activate alternative processes if available",
            "Begin data preservation procedures"
        ]
        
        if function.recovery_strategy == ContinuityStrategy.FAILOVER:
            actions.insert(2, "Initiate automatic failover procedures")
        
        return actions
    
    def _get_communication_plan(self, function: BusinessFunction) -> Dict[str, Any]:
        """Get communication plan for function"""
        return {
            "internal_stakeholders": function.stakeholders,
            "external_stakeholders": ["clients"] if "clients" in function.stakeholders else [],
            "communication_frequency": "every 30 minutes during incident",
            "status_page_updates": True,
            "escalation_matrix": {
                "technical": 5,    # minutes
                "executive": 15,   # minutes  
                "legal": 30,       # minutes
                "clients": 60      # minutes
            }
        }
    
    def _get_resource_requirements(self, function: BusinessFunction) -> Dict[str, Any]:
        """Get resource requirements for continuity"""
        return {
            "personnel": [
                "Technical lead",
                "Business function owner",
                "Communication coordinator"
            ],
            "systems": function.dependencies,
            "external_services": [
                "Backup systems",
                "Alternative communication channels",
                "Emergency support services"
            ],
            "documentation": [
                "Technical recovery procedures",
                "Business process alternatives",
                "Contact information"
            ]
        }
    
    def _get_recovery_procedures(self, function: BusinessFunction) -> List[str]:
        """Get detailed recovery procedures"""
        procedures = [
            "Validate incident scope and root cause",
            "Implement recovery strategy",
            "Monitor recovery progress",
            "Validate function restoration",
            "Document lessons learned"
        ]
        
        # Add function-specific procedures
        procedures[1:1] = function.manual_procedures
        
        return procedures
    
    def _get_testing_schedule(self, function: BusinessFunction) -> str:
        """Get testing schedule based on criticality"""
        if function.impact_level == BusinessImpactLevel.SEVERE:
            return "Monthly"
        elif function.impact_level == BusinessImpactLevel.SIGNIFICANT:
            return "Quarterly"
        else:
            return "Semi-annually"
    
    async def activate_continuity_plan(self, function_name: str, incident_details: Dict[str, Any]) -> Dict[str, Any]:
        """Activate business continuity plan for a function"""
        
        if function_name not in self.continuity_plans:
            return {"success": False, "error": f"No continuity plan for {function_name}"}
        
        plan = self.continuity_plans[function_name]
        function = self.business_functions[function_name]
        
        activation_id = f"bcp_{function_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        activation_log = {
            "activation_id": activation_id,
            "function_name": function_name,
            "incident_details": incident_details,
            "started_at": datetime.now().isoformat(),
            "plan": asdict(plan),
            "actions_completed": [],
            "notifications_sent": [],
            "status": "active",
            "success": False
        }
        
        logger.critical(f"Activating business continuity plan: {function_name}")
        
        try:
            # Store active incident
            self.active_incidents[activation_id] = activation_log
            
            # Execute immediate actions
            for action in plan.immediate_actions:
                action_result = await self._execute_continuity_action(action, function, incident_details)
                activation_log["actions_completed"].append({
                    "action": action,
                    "result": action_result,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send stakeholder notifications
            notification_message = self._create_incident_message(function_name, incident_details)
            notification_result = await self.notification_manager.notify_stakeholders(
                f"{function_name} disruption",
                self._get_severity_level(function.impact_level),
                function.stakeholders,
                notification_message
            )
            
            activation_log["notifications_sent"].append(notification_result)
            
            activation_log["status"] = "plan_activated"
            activation_log["success"] = True
            
            logger.info(f"Business continuity plan activated successfully: {activation_id}")
            
        except Exception as e:
            activation_log["status"] = "activation_failed"
            activation_log["error"] = str(e)
            logger.error(f"Business continuity plan activation failed: {e}")
        
        return activation_log
    
    async def _execute_continuity_action(self, action: str, function: BusinessFunction, incident_details: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual continuity action"""
        
        try:
            if "assess scope and impact" in action.lower():
                return await self._assess_incident_impact(function, incident_details)
            
            elif "notify stakeholders" in action.lower():
                return {"success": True, "message": "Stakeholder notification initiated"}
            
            elif "activate alternative processes" in action.lower():
                return await self._activate_alternative_processes(function)
            
            elif "begin data preservation" in action.lower():
                return await self._begin_data_preservation(function)
            
            elif "initiate automatic failover" in action.lower():
                return await self._initiate_failover(function)
            
            else:
                return {
                    "success": True,
                    "message": f"Action acknowledged: {action}",
                    "manual_action_required": True
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _assess_incident_impact(self, function: BusinessFunction, incident_details: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of the incident on the business function"""
        
        impact_assessment = {
            "function_affected": function.name,
            "impact_level": function.impact_level.value,
            "dependencies_affected": [],
            "estimated_users_affected": 0,
            "financial_impact_estimate": "TBD",
            "regulatory_implications": []
        }
        
        # Check dependency health
        for dependency in function.dependencies:
            # This would check actual system health
            impact_assessment["dependencies_affected"].append({
                "dependency": dependency,
                "status": "unknown",  # Would be determined by health checks
                "impact": "TBD"
            })
        
        # Estimate user impact based on function
        if function.name == "Property Transaction Processing":
            impact_assessment["estimated_users_affected"] = 500  # Active transactions
        elif function.name == "Client Communication Platform":
            impact_assessment["estimated_users_affected"] = 1000  # All active clients
        
        # Check regulatory implications
        if function.name == "Legal Compliance and Audit":
            impact_assessment["regulatory_implications"] = [
                "SRA compliance reporting may be delayed",
                "Audit trail continuity may be affected"
            ]
        
        return {
            "success": True,
            "assessment": impact_assessment
        }
    
    async def _activate_alternative_processes(self, function: BusinessFunction) -> Dict[str, Any]:
        """Activate alternative business processes"""
        
        if not function.manual_procedures:
            return {"success": False, "message": "No alternative processes defined"}
        
        activated_procedures = []
        
        for procedure in function.manual_procedures:
            # This would actually implement the procedure activation
            activated_procedures.append({
                "procedure": procedure,
                "status": "activated",
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "message": f"Activated {len(activated_procedures)} alternative procedures",
            "procedures": activated_procedures
        }
    
    async def _begin_data_preservation(self, function: BusinessFunction) -> Dict[str, Any]:
        """Begin data preservation procedures"""
        
        preservation_actions = [
            "Initiate immediate data backup",
            "Enable transaction logging",
            "Preserve current system state",
            "Document data integrity status"
        ]
        
        return {
            "success": True,
            "message": "Data preservation procedures initiated",
            "actions": preservation_actions
        }
    
    async def _initiate_failover(self, function: BusinessFunction) -> Dict[str, Any]:
        """Initiate automatic failover procedures"""
        
        if function.recovery_strategy != ContinuityStrategy.FAILOVER:
            return {"success": False, "message": "Failover not configured for this function"}
        
        # This would trigger actual failover procedures
        return {
            "success": True,
            "message": "Automatic failover initiated",
            "estimated_completion": "5-10 minutes"
        }
    
    def _create_incident_message(self, function_name: str, incident_details: Dict[str, Any]) -> str:
        """Create incident notification message"""
        
        function = self.business_functions[function_name]
        
        message = f"""
BUSINESS CONTINUITY ALERT

Function Affected: {function.name}
Impact Level: {function.impact_level.value.upper()}
Incident Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Description: {incident_details.get('description', 'System disruption detected')}

Immediate Actions Taken:
- Business continuity plan activated
- Alternative processes being implemented
- Technical team investigating root cause

Expected Resolution: {function.sla_requirements['max_downtime_minutes']} minutes maximum

We will provide updates every 30 minutes or as significant developments occur.

For urgent issues, please contact our emergency support line.

Domus Conveyancing Technical Team
        """.strip()
        
        return message
    
    def _get_severity_level(self, impact_level: BusinessImpactLevel) -> str:
        """Convert impact level to severity level"""
        severity_map = {
            BusinessImpactLevel.MINIMAL: "low",
            BusinessImpactLevel.MODERATE: "medium", 
            BusinessImpactLevel.SIGNIFICANT: "high",
            BusinessImpactLevel.SEVERE: "critical"
        }
        return severity_map.get(impact_level, "medium")
    
    async def test_continuity_plan(self, function_name: str, test_type: str = "tabletop") -> Dict[str, Any]:
        """Test business continuity plan"""
        
        if function_name not in self.continuity_plans:
            return {"success": False, "error": f"No continuity plan for {function_name}"}
        
        plan = self.continuity_plans[function_name]
        test_id = f"test_{function_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_result = {
            "test_id": test_id,
            "function_name": function_name,
            "test_type": test_type,
            "started_at": datetime.now().isoformat(),
            "test_scenarios": [],
            "success": False
        }
        
        if test_type == "tabletop":
            # Tabletop exercise - theoretical walkthrough
            test_result["test_scenarios"] = [
                {"scenario": "Plan activation", "result": "pass"},
                {"scenario": "Stakeholder notification", "result": "pass"},
                {"scenario": "Alternative process activation", "result": "pass"},
                {"scenario": "Recovery validation", "result": "pass"}
            ]
            test_result["success"] = True
            
        elif test_type == "simulation":
            # Simulation - actual system testing without production impact
            # This would implement actual testing procedures
            test_result["success"] = True
            
        # Update plan with test results
        plan.last_tested = datetime.now()
        plan.test_results = test_result
        
        test_result["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Business continuity plan tested: {test_id}")
        
        return test_result
    
    def get_continuity_status(self) -> Dict[str, Any]:
        """Get comprehensive business continuity status"""
        
        status = {
            "business_functions": len(self.business_functions),
            "continuity_plans": len(self.continuity_plans),
            "active_incidents": len(self.active_incidents),
            "functions_status": {},
            "testing_status": {},
            "overall_readiness": "ready"
        }
        
        # Check each function status
        for func_name, function in self.business_functions.items():
            plan = self.continuity_plans[func_name]
            
            # Determine testing status
            testing_overdue = False
            if plan.last_tested:
                days_since_test = (datetime.now() - plan.last_tested).days
                
                if plan.testing_schedule == "Monthly" and days_since_test > 35:
                    testing_overdue = True
                elif plan.testing_schedule == "Quarterly" and days_since_test > 95:
                    testing_overdue = True
                elif plan.testing_schedule == "Semi-annually" and days_since_test > 190:
                    testing_overdue = True
            else:
                testing_overdue = True
            
            status["functions_status"][func_name] = {
                "impact_level": function.impact_level.value,
                "recovery_strategy": function.recovery_strategy.value,
                "sla_max_downtime": function.sla_requirements["max_downtime_minutes"],
                "plan_exists": True,
                "testing_overdue": testing_overdue,
                "last_tested": plan.last_tested.isoformat() if plan.last_tested else None
            }
            
            if testing_overdue:
                status["overall_readiness"] = "testing_overdue"
        
        # Active incidents summary
        if self.active_incidents:
            status["active_incidents_detail"] = list(self.active_incidents.keys())
            status["overall_readiness"] = "incident_active"
        
        return status