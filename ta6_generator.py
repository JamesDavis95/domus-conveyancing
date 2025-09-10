from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

FIELDS = [
    ("Property Address", "address"),
    ("Seller Name", "seller"),
    ("Tenure (Freehold/Leasehold)", "tenure"),
    ("If leasehold, years remaining", "lease_years"),
    ("Alterations/Extensions done?", "alterations"),
    ("Disputes/Complaints?", "disputes"),
    ("Notices/Aware of proposals?", "notices"),
    ("Guarantees (FENSA/Gas/Electrical)?", "certs"),
    ("Flood history?", "flood"),
]

def build_ta6_pdf(path: str, data: dict):
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 25*mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, "TA6 Property Information (Summary)"); y -= 12*mm
    c.setFont("Helvetica", 10)
    for label,key in FIELDS:
        val = str(data.get(key,""))[:140]
        c.drawString(20*mm, y, f"{label}: {val}"); y -= 8*mm
    c.showPage(); c.save()
