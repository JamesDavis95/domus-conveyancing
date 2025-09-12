"""
SLA Management Module for LA System
Handles service level agreements, deadlines, and escalations
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from db import get_db

logger = logging.getLogger(__name__)

class SLAManager:
    """Manages SLA timelines and escalations"""
    
    def __init__(self):
        # SLA configuration (working days)
        self.sla_config = {
            "llc1": {"standard": 10, "priority": 5, "urgent": 2},
            "con29": {"standard": 10, "priority": 5, "urgent": 2}, 
            "con29o": {"standard": 15, "priority": 10, "urgent": 5},
            "combined": {"standard": 15, "priority": 10, "urgent": 5}
        }
        
        # Escalation thresholds (days before due date)
        self.escalation_thresholds = {
            "reminder": 3,      # Send reminder 3 days before due
            "at_risk": 2,       # Mark at risk 2 days before due  
            "overdue": 0,       # Mark overdue on due date
            "urgent_escalation": -1  # Urgent escalation 1 day after due
        }
    
    async def calculate_sla_dates(self, matter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate SLA due dates based on matter requirements"""
        try:
            products = []
            if matter_data.get("llc1_requested") == "true":
                products.append("llc1")
            if matter_data.get("con29_requested") == "true":
                products.append("con29")
            if matter_data.get("con29o_requested") == "true":
                products.append("con29o")
            
            priority = matter_data.get("priority", "standard")
            
            # Determine overall SLA (use longest for combined requests)
            if len(products) > 1:
                sla_days = self.sla_config["combined"][priority]
            elif products:
                sla_days = self.sla_config[products[0]][priority]
            else:
                sla_days = self.sla_config["con29"][priority]  # Default
            
            # Calculate business days
            start_date = datetime.now()
            due_date = self._add_business_days(start_date, sla_days)
            
            # Calculate escalation dates
            reminder_date = self._add_business_days(start_date, sla_days - self.escalation_thresholds["reminder"])
            at_risk_date = self._add_business_days(start_date, sla_days - self.escalation_thresholds["at_risk"])
            
            return {
                "sla_days": sla_days,
                "start_date": start_date,
                "due_date": due_date,
                "reminder_date": reminder_date,
                "at_risk_date": at_risk_date,
                "products": products,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"SLA calculation failed: {e}")
            return {"error": str(e)}
    
    def _add_business_days(self, start_date: datetime, business_days: int) -> datetime:
        """Add business days (excluding weekends)"""
        current_date = start_date
        days_added = 0
        
        while days_added < business_days:
            current_date += timedelta(days=1)
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                days_added += 1
        
        return current_date
    
    async def check_sla_status(self, matter_id: str, db: Session) -> Dict[str, Any]:
        """Check current SLA status for a matter"""
        try:
            from la.models import LAMatter, LASLAEvent
            
            matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
            if not matter:
                return {"error": "Matter not found"}
            
            if not matter.sla_due_date:
                return {"status": "no_sla", "message": "No SLA set"}
            
            now = datetime.now()
            due_date = matter.sla_due_date
            days_until_due = (due_date - now).days
            
            # Determine status
            if days_until_due > self.escalation_thresholds["at_risk"]:
                status = "on_time"
                escalation_level = 0
            elif days_until_due > self.escalation_thresholds["overdue"]:
                status = "at_risk"  
                escalation_level = 1
            elif days_until_due >= self.escalation_thresholds["urgent_escalation"]:
                status = "overdue"
                escalation_level = 2
            else:
                status = "urgent_overdue"
                escalation_level = 3
            
            return {
                "matter_id": matter_id,
                "status": status,
                "escalation_level": escalation_level,
                "days_until_due": days_until_due,
                "due_date": due_date.isoformat(),
                "current_status": matter.status
            }
            
        except Exception as e:
            logger.error(f"SLA status check failed: {e}")
            return {"error": str(e)}
    
    async def create_sla_event(self, matter_id: str, event_type: str, db: Session) -> bool:
        """Create SLA tracking event"""
        try:
            from la.models import LASLAEvent, LAMatter
            
            matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
            if not matter:
                return False
            
            sla_event = LASLAEvent(
                matter_id=matter_id,
                event_type=event_type,
                due_date=matter.sla_due_date or datetime.now() + timedelta(days=10),
                escalation_level=0 if event_type == "sla_started" else 1
            )
            
            db.add(sla_event)
            db.commit()
            
            logger.info(f"Created SLA event {event_type} for matter {matter_id}")
            return True
            
        except Exception as e:
            logger.error(f"SLA event creation failed: {e}")
            return False
    
    async def get_overdue_matters(self, db: Session) -> List[Dict[str, Any]]:
        """Get all overdue matters for dashboard"""
        try:
            from la.models import LAMatter
            
            now = datetime.now()
            overdue_matters = db.query(LAMatter).filter(
                LAMatter.sla_due_date < now,
                LAMatter.status.notin_(["issued", "cancelled"])
            ).all()
            
            results = []
            for matter in overdue_matters:
                days_overdue = (now - matter.sla_due_date).days
                results.append({
                    "id": matter.id,
                    "ref": matter.ref,
                    "address": matter.address,
                    "status": matter.status,
                    "assigned_to": matter.assigned_to,
                    "days_overdue": days_overdue,
                    "priority": matter.priority,
                    "due_date": matter.sla_due_date.isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Overdue matters query failed: {e}")
            return []
    
    async def get_at_risk_matters(self, db: Session) -> List[Dict[str, Any]]:
        """Get matters approaching SLA deadline"""
        try:
            from la.models import LAMatter
            
            now = datetime.now()
            risk_threshold = now + timedelta(days=self.escalation_thresholds["at_risk"])
            
            at_risk_matters = db.query(LAMatter).filter(
                LAMatter.sla_due_date <= risk_threshold,
                LAMatter.sla_due_date >= now,
                LAMatter.status.notin_(["issued", "cancelled"])
            ).all()
            
            results = []
            for matter in at_risk_matters:
                days_until_due = (matter.sla_due_date - now).days
                results.append({
                    "id": matter.id,
                    "ref": matter.ref, 
                    "address": matter.address,
                    "status": matter.status,
                    "assigned_to": matter.assigned_to,
                    "days_until_due": days_until_due,
                    "priority": matter.priority,
                    "due_date": matter.sla_due_date.isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"At-risk matters query failed: {e}")
            return []
    
    async def update_matter_sla_status(self, matter_id: str, db: Session) -> bool:
        """Update matter SLA status based on current timeline"""
        try:
            from la.models import LAMatter
            
            sla_status = await self.check_sla_status(matter_id, db)
            if "error" in sla_status:
                return False
            
            matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
            if matter:
                matter.sla_status = sla_status["status"]
                db.commit()
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"SLA status update failed: {e}")
            return False

# Global SLA manager instance
sla_manager = SLAManager()