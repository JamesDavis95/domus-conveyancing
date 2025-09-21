#!/usr/bin/env python3
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Domus Global")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Domus Planning Platform - Integrated Planning Services</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1e1e1e; color: white; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            h1 { color: #4CAF50; margin-bottom: 20px; }
            .status { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 Domus Planning Platform</h1>
            <h2>Intelligent Planning & Development</h2>
            <div class="status">
                <h3>✅ Platform Status: ONLINE</h3>
                <p>Your comprehensive planning intelligence and property development platform is now live!</p>
            </div>
            <div class="status">
                <h3>🚀 Features Available</h3>
                <ul style="text-align: left;">
                    <li>Planning Application Management</li>
                    <li>Development Intelligence</li>
                    <li>Land Charges Search Processing</li>
                    <li>Policy Compliance Checking</li>
                    <li>Council Dashboard & Analytics</li>
                </ul>
            </div>
            <p><strong>Platform successfully deployed and ready for use!</strong></p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    return {"status": "healthy", "platform": "Domus Global", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)