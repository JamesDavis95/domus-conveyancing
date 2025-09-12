"""
Quality Assurance Workflow Module
Handles review processes, approvals, and quality control
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from db import get_db

logger = logging.getLogger(__name__)

class QAWorkflow:
    """Manages quality assurance and review processes"""
    
    def __init__(self):
        # QA configuration
        self.qa_config = {
            "sample_rates": {
                "new_caseworker": 1.0,    # 100% of new caseworker matters
                "standard": 0.1,          # 10% random sample
                "priority": 0.3,          # 30% of priority matters
                "urgent": 1.0             # 100% of urgent matters
            },
            "auto_approve_thresholds": {
                "confidence_score": 0.95,  # Auto-approve if AI confidence > 95%
                "risk_level": "LOW",       # Only auto-approve LOW risk
                "caseworker_experience": 24  # Auto-approve experienced caseworkers (months)
            }
        }
    
    async def determine_qa_requirement(self, matter_data: Dict[str, Any], caseworker_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Determine if matter requires QA review"""
        try:
            qa_required = False
            qa_reason = []
            review_type = "standard"
            
            priority = matter_data.get("priority", "standard")
            
            # Check priority-based requirements
            if priority == "urgent":
                qa_required = True
                qa_reason.append("urgent_priority")
                review_type = "priority"
            elif priority == "priority":
                import random
                if random.random() < self.qa_config["sample_rates"]["priority"]:
                    qa_required = True
                    qa_reason.append("priority_sample")
                    review_type = "priority"
            
            # Check caseworker experience
            if caseworker_data:
                experience_months = caseworker_data.get("experience_months", 0)
                if experience_months < 6:  # New caseworker
                    qa_required = True
                    qa_reason.append("new_caseworker")
                    review_type = "standard"
            
            # Check AI confidence levels
            findings = matter_data.get("findings", [])
            if findings:
                avg_confidence = sum(f.get("confidence", 0) for f in findings) / len(findings)
                if avg_confidence < 0.8:  # Low AI confidence
                    qa_required = True
                    qa_reason.append("low_ai_confidence")
            
            # Check risk levels
            risks = matter_data.get("risks", [])
            high_risk_count = sum(1 for r in risks if r.get("severity") == "HIGH")
            if high_risk_count > 0:
                qa_required = True  
                qa_reason.append("high_risk_findings")
                review_type = "priority"
            
            # Random sampling for quality control
            if not qa_required:
                import random
                if random.random() < self.qa_config["sample_rates"]["standard"]:
                    qa_required = True
                    qa_reason.append("random_sample")
            
            return {
                "qa_required": qa_required,
                "review_type": review_type,
                "reasons": qa_reason,
                "estimated_review_time": self._estimate_review_time(review_type, len(findings))
            }
            
        except Exception as e:
            logger.error(f"QA requirement determination failed: {e}")
            return {"qa_required": True, "review_type": "standard", "reasons": ["error_fallback"]}
    
    def _estimate_review_time(self, review_type: str, finding_count: int) -> int:
        """Estimate review time in minutes"""
        base_times = {"standard": 15, "priority": 25, "random_sample": 10}
        base = base_times.get(review_type, 15)
        return base + (finding_count * 2)  # 2 mins per finding
    
    async def assign_reviewer(self, matter_id: str, review_type: str, db: Session) -> Optional[str]:
        """Assign available reviewer to matter"""
        try:
            from la.models import LAUser, LAQAReview
            
            # Find available reviewers
            reviewers = db.query(LAUser).filter(
                LAUser.can_review == "true",
                LAUser.is_active == "true"
            ).all()
            
            if not reviewers:
                logger.warning("No available reviewers found")
                return None
            
            # Check current workloads
            reviewer_workloads = {}
            for reviewer in reviewers:
                active_reviews = db.query(LAQAReview).filter(
                    LAQAReview.reviewer_id == reviewer.id,
                    LAQAReview.status.in_(["pending", "in_progress"])
                ).count()
                
                reviewer_workloads[reviewer.id] = {
                    "user": reviewer,
                    "active_reviews": active_reviews,
                    "capacity": reviewer.workload_capacity
                }
            
            # Assign to reviewer with lowest workload
            available_reviewers = [
                r for r in reviewer_workloads.values() 
                if r["active_reviews"] < r["capacity"]
            ]
            
            if not available_reviewers:
                logger.warning("All reviewers at capacity")
                return None
            
            # Sort by workload (lowest first)
            available_reviewers.sort(key=lambda x: x["active_reviews"])
            selected_reviewer = available_reviewers[0]["user"]
            
            return selected_reviewer.id
            
        except Exception as e:
            logger.error(f"Reviewer assignment failed: {e}")
            return None
    
    async def create_qa_review(self, matter_id: str, review_type: str, db: Session) -> Optional[str]:
        """Create QA review record"""
        try:
            from la.models import LAQAReview
            
            reviewer_id = await self.assign_reviewer(matter_id, review_type, db)
            if not reviewer_id:
                return None
            
            # Get reviewer details
            from la.models import LAUser
            reviewer = db.query(LAUser).filter(LAUser.id == reviewer_id).first()
            
            qa_review = LAQAReview(
                matter_id=matter_id,
                reviewer_id=reviewer_id,
                reviewer_name=reviewer.full_name if reviewer else "Unknown",
                review_type=review_type,
                status="pending"
            )
            
            db.add(qa_review)
            db.commit()
            
            logger.info(f"Created QA review {qa_review.id} for matter {matter_id}")
            return qa_review.id
            
        except Exception as e:
            logger.error(f"QA review creation failed: {e}")
            return None
    
    async def start_review(self, review_id: str, db: Session) -> bool:
        """Start QA review process"""
        try:
            from la.models import LAQAReview, LAMatter
            
            review = db.query(LAQAReview).filter(LAQAReview.id == review_id).first()
            if not review:
                return False
            
            # Update review status
            review.status = "in_progress"
            review.started_at = datetime.now()
            
            # Update matter status
            matter = db.query(LAMatter).filter(LAMatter.id == review.matter_id).first()
            if matter:
                matter.status = "qa_review"
                matter.qa_started_at = datetime.now()
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Review start failed: {e}")
            return False
    
    async def submit_review_decision(self, review_id: str, decision_data: Dict[str, Any], db: Session) -> bool:
        """Submit QA review decision"""
        try:
            from la.models import LAQAReview, LAMatter, LAFinding, LARisk
            
            review = db.query(LAQAReview).filter(LAQAReview.id == review_id).first()
            if not review:
                return False
            
            matter = db.query(LAMatter).filter(LAMatter.id == review.matter_id).first()
            if not matter:
                return False
            
            decision = decision_data.get("decision")  # approved|rejected|needs_changes
            
            # Update review record
            review.status = decision
            review.completed_at = datetime.now()
            review.reviewer_comments = decision_data.get("comments", "")
            review.findings_approved = decision_data.get("findings_approved", 0)
            review.findings_rejected = decision_data.get("findings_rejected", 0)
            review.answers_modified = decision_data.get("answers_modified", 0)
            
            # Apply any changes
            changes = decision_data.get("changes", [])
            change_summary = []
            
            for change in changes:
                if change["type"] == "finding_modification":
                    finding = db.query(LAFinding).filter(LAFinding.id == change["finding_id"]).first()
                    if finding:
                        old_answer = finding.answer
                        finding.answer = change["new_answer"] 
                        finding.confidence = change.get("new_confidence", finding.confidence)
                        change_summary.append(f"Modified finding {finding.code}: {old_answer} -> {change['new_answer']}")
                
                elif change["type"] == "risk_modification":
                    risk = db.query(LARisk).filter(LARisk.id == change["risk_id"]).first()
                    if risk:
                        old_severity = risk.severity
                        risk.severity = change["new_severity"]
                        risk.message = change.get("new_message", risk.message)
                        change_summary.append(f"Modified risk {risk.code}: {old_severity} -> {change['new_severity']}")
            
            review.change_summary = json.dumps(change_summary)
            
            # Update matter status based on decision
            if decision == "approved":
                matter.status = "approved"
                matter.approved_at = datetime.now()
            elif decision == "rejected":
                matter.status = "in_progress"  # Send back to caseworker
            elif decision == "needs_changes":
                matter.status = "in_progress"  # Send back with specific changes
            
            db.commit()
            
            logger.info(f"QA review {review_id} completed with decision: {decision}")
            return True
            
        except Exception as e:
            logger.error(f"Review decision submission failed: {e}")
            return False
    
    async def get_pending_reviews(self, reviewer_id: Optional[str] = None, db: Session = None) -> List[Dict[str, Any]]:
        """Get pending QA reviews"""
        try:
            from la.models import LAQAReview, LAMatter
            
            query = db.query(LAQAReview).filter(LAQAReview.status == "pending")
            
            if reviewer_id:
                query = query.filter(LAQAReview.reviewer_id == reviewer_id)
            
            reviews = query.join(LAMatter).all()
            
            results = []
            for review in reviews:
                matter = review.matter
                results.append({
                    "review_id": review.id,
                    "matter_id": review.matter_id,
                    "matter_ref": matter.ref,
                    "address": matter.address,
                    "review_type": review.review_type,
                    "assigned_at": review.assigned_at.isoformat(),
                    "estimated_time": self._estimate_review_time(review.review_type, 5),  # Rough estimate
                    "priority": matter.priority,
                    "caseworker": matter.assigned_to
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Pending reviews query failed: {e}")
            return []
    
    async def get_review_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Get QA dashboard statistics"""
        try:
            from la.models import LAQAReview
            
            # Get review statistics
            total_pending = db.query(LAQAReview).filter(LAQAReview.status == "pending").count()
            total_in_progress = db.query(LAQAReview).filter(LAQAReview.status == "in_progress").count()
            total_completed_today = db.query(LAQAReview).filter(
                LAQAReview.completed_at >= datetime.now().replace(hour=0, minute=0, second=0),
                LAQAReview.status.in_(["approved", "rejected", "needs_changes"])
            ).count()
            
            # Get approval rates
            completed_this_week = db.query(LAQAReview).filter(
                LAQAReview.completed_at >= datetime.now() - timedelta(days=7),
                LAQAReview.status.in_(["approved", "rejected", "needs_changes"])
            ).all()
            
            approved_count = sum(1 for r in completed_this_week if r.status == "approved")
            total_completed = len(completed_this_week)
            approval_rate = (approved_count / total_completed * 100) if total_completed > 0 else 0
            
            return {
                "pending_reviews": total_pending,
                "in_progress_reviews": total_in_progress,
                "completed_today": total_completed_today,
                "approval_rate_7_days": round(approval_rate, 1),
                "total_completed_7_days": total_completed
            }
            
        except Exception as e:
            logger.error(f"QA dashboard data query failed: {e}")
            return {}

# Global QA workflow instance
qa_workflow = QAWorkflow()