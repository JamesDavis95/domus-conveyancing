import io, json, zipfile
from pathlib import Path
from typing import Dict, Any

def build_pack(rec: Dict[str,Any], extras: Dict[str, bytes] | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("extracted.json", json.dumps(rec.get("extracted_json") or {}, indent=2))
        z.writestr("risk.json", json.dumps(rec.get("risk_json") or {}, indent=2))
        # Include any files you already generated if present
        client_pdf = Path("client_summary.pdf")
        if client_pdf.exists(): z.write(str(client_pdf), "client_summary.pdf")
        ta6_pdf = Path("ta6_summary.pdf")
        if ta6_pdf.exists(): z.write(str(ta6_pdf), "TA6-summary.pdf")
        if extras:
            for k,v in extras.items():
                z.writestr(k, v)
    return buf.getvalue()
