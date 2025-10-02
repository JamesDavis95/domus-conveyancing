from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def root():
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head><title>🚀 RAILWAY DEPLOYMENT TEST</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h1 style="color: #1e40af;">🎉 RAILWAY DEPLOYMENT SUCCESSFUL!</h1>
    <p style="font-size: 20px;">New deployment is working - timestamp: 2025-10-02 10:15</p>
    <p style="background: #f0f9ff; padding: 20px; border-radius: 10px;">
        ✅ Docker build worked<br>
        ✅ FastAPI app started<br>
        ✅ Beautiful interface ready
    </p>
</body>
</html>
""")

@app.get("/test")
def test():
    return {"status": "SUCCESS", "timestamp": "2025-10-02", "message": "Railway deployment WORKING"}

@app.get("/health")
def health():
    return {"status": "healthy", "deployment": "fresh", "timestamp": "2025-10-02"}