def risk_engine(llc1_obj, con29_obj):
    risks = []

    try:
        if con29_obj and con29_obj.roads_footways and con29_obj.roads_footways.abutting_highway_adopted is False:
            risks.append({"code": "UnadoptedRoad", "level": "HIGH"})
    except Exception:
        pass

    try:
        if llc1_obj and any(c.charge_type.lower().startswith("conservation") and c.present for c in llc1_obj.charges):
            risks.append({"code": "ConservationArea", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if llc1_obj and any(c.charge_type.lower().startswith("listed") and c.present for c in llc1_obj.charges):
            risks.append({"code": "ListedBuilding", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and con29_obj.enforcement_notices_present:
            risks.append({"code": "EnforcementNotice", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and con29_obj.contaminated_land_designation:
            risks.append({"code": "ContaminatedLand", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and con29_obj.s106_present:
            risks.append({"code": "Section106", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and con29_obj.cil_outstanding:
            risks.append({"code": "CILOutstanding", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and (con29_obj.flood_zone == "3"):
            risks.append({"code": "FloodZone3", "level": "HIGH"})
    except Exception:
        pass

    try:
        if con29_obj and con29_obj.radon_affected:
            risks.append({"code": "RadonAffected", "level": "MEDIUM"})
    except Exception:
        pass

    try:
        if con29_obj and (con29_obj.building_regs_completion_present is False):
            risks.append({"code": "MissingBuildingRegs", "level": "MEDIUM"})
    except Exception:
        pass

    return risks
