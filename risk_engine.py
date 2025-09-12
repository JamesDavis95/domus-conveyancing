RULES = [
    {"code":"FLOOD_ZONE_2","severity":"medium","needles":["flood zone 2","flood risk 2","flood zone two"]},
    {"code":"LISTED_BUILDING","severity":"high","needles":["listed building"]},
    {"code":"CONSERVATION_AREA","severity":"medium","needles":["conservation area"]},
    {"code":"CIL_OR_S106","severity":"medium","needles":["cil","section 106","s106"]},
    {"code":"UNADOPTED_ROAD","severity":"medium","needles":["unadopted road","not adopted highway"]},
    {"code":"RADON_AFFECTED","severity":"low","needles":["radon protection","radon affected"]},
    {"code":"ENFORCEMENT_NOTICE","severity":"high","needles":["enforcement notice"]},
]
def run(text: str):
    t = (text or "").lower()
    findings, risks = [], []
    for r in RULES:
        if any(n in t for n in r["needles"]):
            risks.append({
                "code": r["code"],
                "severity": r["severity"],
                "explanation": f"Detected {r['code']} by keyword match"
            })
    return {"findings": findings, "risks": risks}
