#!/usr/bin/env python3
"""
Domus Planning Platform - Clean Frontend Demo
Serving the 4-Pillar AI Planning System Interface
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# Initialize clean demo app
app = FastAPI(
    title="Domus - AI Operating System for Planning",
    description="4-Pillar AI Planning System: Property API + Planning AI + Auto-Docs + Offsets Marketplace",
    version="4.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the clean 4-pillar planning interface"""
    with open('frontend/platform_clean.html', 'r') as f:
        return f.read()

@app.get("/health")
async def health_check():
    """Health check for the clean platform demo"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "platform": "Domus Planning AI System",
        "mode": "clean_demo",
        "pillars": {
            "property_api": "demo_ready",
            "planning_ai": "demo_ready", 
            "auto_docs": "demo_ready",
            "offsets_marketplace": "demo_ready"
        },
        "workflow": "Site Input → Property API → Planning AI → Auto-Docs → Submit OR Offsets"
    }

@app.get("/api/demo/analyze")
async def demo_analysis():
    """Demo API endpoint for site analysis"""
    return {
        "site_address": "123 Oxford Street, London",
        "approval_probability": 73,
        "confidence": 92,
        "constraints": [
            {"type": "Conservation Area", "severity": "medium"},
            {"type": "Flood Zone 2", "severity": "low"},
            {"type": "Tree Preservation Order", "severity": "low"}
        ],
        "recommendations": [
            "Consider heritage impact assessment for Conservation Area compliance",
            "Reduce building footprint by 10% to mitigate flood risk concerns",
            "Retain existing mature trees in landscape design"
        ],
        "property_data": {
            "land_registry": "Freehold title, last sold £2.1M (2019)",
            "epc_rating": "C (72/100)",
            "flood_risk": "Zone 1 (Low probability)", 
            "planning_history": "3 applications (2 approved, 1 refused)"
        }
    }

@app.get("/api/offsets/stats")
async def offsets_stats():
    """Offsets marketplace statistics"""
    return {
        "total_gmv": 4700000,
        "units_traded": 12847,
        "active_projects": 189,
        "success_rate": 94,
        "supply_listings": 347,
        "demand_listings": 127,
        "average_price": 42.50,
        "matches_today": 23
    }

@app.get("/api/planning/analytics")
async def planning_analytics():
    """Planning analytics and LPA performance"""
    return {
        "total_applications": 847,
        "average_approval_rate": 74,
        "lpas_covered": 328,
        "prediction_accuracy": 89,
        "top_performers": [
            {"name": "South Cambridgeshire", "rate": 94},
            {"name": "Elmbridge Borough", "rate": 91},
            {"name": "Test Valley Borough", "rate": 88}
        ],
        "challenging_lpas": [
            {"name": "Brighton & Hove", "rate": 42},
            {"name": "Camden Council", "rate": 38},
            {"name": "Islington Council", "rate": 35}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Domus Clean Planning Platform...")
    print("🎯 4-Pillar AI System: Property API + Planning AI + Auto-Docs + Offsets")
    uvicorn.run(app, host="0.0.0.0", port=8001)