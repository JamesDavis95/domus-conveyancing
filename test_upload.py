import requests

# Replace with your actual PDF path and server URL
pdf_path = "dummy.pdf"
url = "http://localhost:8000/la/matters/ingest"

with open(pdf_path, "rb") as f:
    files = {"file": (pdf_path, f, "application/pdf")}
    # You can also use 'files' instead of 'file' if needed
    response = requests.post(url, files=files)
    print("Status:", response.status_code)
    print("Response:", response.text)
