import requests

pdf_path = "dummy.pdf"  # Change to your PDF file if needed
url = "http://localhost:8000/la/matters/ingest"

with open(pdf_path, "rb") as f:
    files = {"file": (pdf_path, f, "application/pdf")}
    try:
        response = requests.post(url, files=files)
        print("Status:", response.status_code)
        print("Headers:", response.headers)
        try:
            print("JSON:", response.json())
        except Exception:
            print("Text:", response.text)
    except Exception as e:
        print("Request failed:", e)
