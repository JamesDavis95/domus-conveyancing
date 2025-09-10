import tempfile, subprocess, os
from pdfminer.high_level import extract_text
import fitz  # PyMuPDF

def _extract_pdfminer(path: str) -> str:
    try:
        return extract_text(path) or ""
    except Exception:
        return ""

def _page_count(path: str) -> int:
    try:
        with fitz.open(path) as doc:
            return len(doc)
    except Exception:
        return 0

def extract_text_with_ocr(b: bytes) -> str:
    with tempfile.TemporaryDirectory() as td:
        pdf_in = os.path.join(td, "in.pdf")
        pdf_ocr = os.path.join(td, "ocr.pdf")
        with open(pdf_in, "wb") as f:
            f.write(b)
        txt = _extract_pdfminer(pdf_in)
        if len(txt.strip()) > 200:
            return txt
        # OCR fallback
        try:
            subprocess.run(
                ["ocrmypdf","--skip-text",pdf_in,pdf_ocr],
                check=True, capture_output=True
            )
            return _extract_pdfminer(pdf_ocr)
        except Exception:
            return txt  # return whatever we got
