from pydantic import BaseModel
from typing import Optional, List

class Evidence(BaseModel):
    file_id: str
    page: Optional[int] = None
    note: Optional[str] = None

class Charge(BaseModel):
    charge_type: str
    present: bool
    reference: Optional[str] = None
    source: Optional[str] = None
    evidence: Optional[Evidence] = None

class LLC1(BaseModel):
    charges: List[Charge] = []

class PlanningDecision(BaseModel):
    ref: str
    date: Optional[str] = None
    description: Optional[str] = None
    decision: Optional[str] = None
    evidence: Optional[Evidence] = None

class RoadsFootways(BaseModel):
    abutting_highway_adopted: Optional[bool] = None
    authority: Optional[str] = None
    evidence: Optional[Evidence] = None

class Con29(BaseModel):
    planning_decisions: List[PlanningDecision] = []
    roads_footways: Optional[RoadsFootways] = None
    enforcement_notices_present: Optional[bool] = None
    contaminated_land_designation: Optional[bool] = None
    s106_present: Optional[bool] = None
    cil_outstanding: Optional[bool] = None
    flood_zone: Optional[str] = None
    radon_affected: Optional[bool] = None
    building_regs_completion_present: Optional[bool] = None
