from typing import Dict, Any, List

def risk_engine(extracted: Dict[str, Any], conv: Dict[str, Any]) -> Dict[str, Any]:
    """Return risk score [0..1], issues, summary, confidence map."""
    issues: List[str] = []
    score = 0.0

    flood = ((extracted or {}).get("flood_zone") or "").lower()
    if "zone 3" in flood:
        score += 0.6; issues.append("Environment Agency Flood Zone 3 indicated.")
    elif "zone 2" in flood:
        score += 0.35; issues.append("Environment Agency Flood Zone 2 indicated.")
    elif "surface water" in flood:
        score += 0.15; issues.append("Surface water flood screening mention.")

    llc1 = (conv or {}).get("llc1", {})
    if llc1.get("tpo"):
        score += 0.15; issues.append("Tree Preservation Order present.")
    if llc1.get("conservation_area"):
        score += 0.2; issues.append("Conservation Area constraints apply.")
    if llc1.get("s106"):
        score += 0.2; issues.append("Section 106 obligations present.")
    if llc1.get("cil"):
        score += 0.05; issues.append("Community Infrastructure Levy (CIL) may apply.")

    # Clamp
    score = max(0.0, min(1.0, score))

    if score >= 0.75: summary = "High"
    elif score >= 0.5: summary = "Elevated"
    elif score >= 0.2: summary = "Moderate"
    else: summary = "Low"

    confidence = {
        "flood_zone": "high" if flood else "low",
        "road_status": (conv or {}).get("con29", {}).get("road_status_confidence") or "low",
    }

    return {
        "risk_score": round(score, 2),
        "issues": issues,
        "summary": summary,
        "confidence": confidence
    }
