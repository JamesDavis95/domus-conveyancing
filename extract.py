import re
from pathlib import Path

def extract_text_from_pdf(path):
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text
    except Exception:
        return ""

def extract_fields(text):
    address = re.search(r"Address: (.+)", text)
    title = re.search(r"Title Number: (\w+)", text)
    uprn = re.search(r"UPRN: (\d+)", text)
    postcode = re.search(r"Postcode: ([A-Z0-9 ]{5,8})", text, re.I)
    risks = []
    if "contaminated" in text.lower():
        risks.append({"code": "CONTAM", "level": "high", "description": "Possible contamination"})
    return {
        "address": address.group(1) if address else "",
        "title_number": title.group(1) if title else "",
        "uprn": uprn.group(1) if uprn else "",
        "postcode": postcode.group(1) if postcode else "",
        "risks": risks
    }