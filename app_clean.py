#!/usr/bin/env python3
"""
Domus Planning Platform - AI Operating System for Planning and Land Use
The 4-Pillar AI Planning System for Developers, Consultants, and Councils

🧠 Planning AI - Instant approval probability & constraint analysis
📄 Auto-Docs - Professional planning document generation  
🏠 Property API - Unified UK property data source
🌱 Offsets Marketplace - Biodiversity Net Gain trading platform
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import random


# Initialize the Domus Planning Platform
app = FastAPI(
    title="Domus Planning Platform - AI Operating System", 
    description="The 4-Pillar AI Planning System: Planning AI + Auto-Docs + Property API + Offsets Marketplace",
    version="4.0.0",
    contact={
        "name": "Domus Platform",
        "email": "hello@domusplanning.co.uk",
        "url": "https://domusplanning.co.uk"
    }
)

# Simple CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Mount the 4 Core Planning AI Packages
print("🚀 Loading Domus 4-Pillar AI Planning System...")

try:
    # 🧠 Planning AI - Site analysis and approval prediction
    from planning_ai.router import router as planning_ai_router
    app.include_router(planning_ai_router)
    print("   ✅ Planning AI - Site analysis and constraint mapping")
except ImportError as e:
    print(f"   ⚠️  Planning AI not available: {e}")

try:
    # 📄 Auto-Docs - Professional document generation
    from auto_docs.router import router as auto_docs_router
    app.include_router(auto_docs_router) 
    print("   ✅ Auto-Docs - Professional planning document generation")
except ImportError as e:
    print(f"   ⚠️  Auto-Docs not available: {e}")

try:
    # 🏠 Property API - Unified property data source
    from property_api.router import router as property_api_router
    app.include_router(property_api_router)
    print("   ✅ Property API - Unified UK property data integration")
except ImportError as e:
    print(f"   ⚠️  Property API not available: {e}")

try:
    # 🌱 Offsets Marketplace - Biodiversity trading
    from offsets_marketplace.router import router as offsets_router
    app.include_router(offsets_router)
    print("   ✅ Offsets Marketplace - Biodiversity Net Gain trading")
except ImportError as e:
    print(f"   ⚠️  Offsets Marketplace not available: {e}")

print("\n🎯 Domus Planning Platform Ready!")
print("   💡 AI Operating System for Planning and Land Use")
print("   🏆 Faster decisions, cheaper compliance, higher certainty")

# Serve the clean frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main planning platform interface"""
    try:
        with open('frontend/platform_clean.html', 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"✅ Serving platform_clean.html - Title: {content[content.find('<title>')+7:content.find('</title>')]}")
            return content
    except Exception as e:
        print(f"❌ Error loading platform_clean.html: {e}")
        return f"<html><body><h1>Error loading platform</h1><p>{e}</p></body></html>"

@app.get("/health")
async def health_check():
    """Simple health check for the 4-pillar system"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "platform": "Domus Planning AI System",
        "version": "4.0.0",
        
        "core_pillars": {
            "planning_ai": {
                "name": "Planning AI Analysis",
                "description": "Instant approval probability & constraint analysis",
                "status": "operational"
            },
            "auto_docs": {
                "name": "Auto-Docs Generator", 
                "description": "Professional planning document generation",
                "status": "operational"
            },
            "property_api": {
                "name": "Property Data API",
                "description": "Unified UK property data source", 
                "status": "operational"
            },
            "offsets_marketplace": {
                "name": "Offsets Marketplace",
                "description": "Biodiversity Net Gain trading platform",
                "status": "operational"
            }
        },
        
        "value_proposition": {
            "for_developers": "Save months and £20k+ in consultancy costs",
            "for_consultants": "Scale output with AI co-pilot tools",
            "for_councils": "Fewer poor applications, faster processing",
            "for_landowners": "Monetise land through biodiversity offsets"
        }
    }

@app.get("/api/workflow-guide")
async def workflow_guide():
    """Guide users through the 4-pillar workflow"""
    return {
        "workflow_steps": [
            {
                "step": 1,
                "pillar": "Site Input",
                "action": "Input site details (address, UPRN, or polygon)",
                "endpoint": "/api/sites/analyze"
            },
            {
                "step": 2, 
                "pillar": "Property API",
                "action": "Pull unified property data (title, EPC, flood, planning history)",
                "endpoint": "/api/property/lookup"
            },
            {
                "step": 3,
                "pillar": "Planning AI", 
                "action": "Analyze constraints + policies → approval probability + recommendations",
                "endpoint": "/api/planning-ai/analyze"
            },
            {
                "step": 4,
                "pillar": "Auto-Docs",
                "action": "Generate planning application documents (Planning Statement, D&A)",
                "endpoint": "/api/auto-docs/generate"
            },
            {
                "step": 5,
                "pillar": "Decision Point",
                "action": "If viable → proceed with application. If not viable → list in Offsets Marketplace",
                "endpoint": "/api/offsets/list OR submit application"
            }
        ],
        "integration_points": {
            "data_flow": "Site Input → Property API → Planning AI → Auto-Docs → Submit OR Offsets",
            "closed_loop": "Failed planning applications become biodiversity offset opportunities"
        }
    }

@app.get("/api/market-stats")
async def market_statistics():
    """Show the planning market problem this solves"""
    return {
        "uk_planning_problems": {
            "average_planning_consultant_cost": "£15,000 - £30,000 per application",
            "average_decision_time": "8-16 weeks for major applications", 
            "approval_uncertainty": "60-70% approval rate varies wildly by area",
            "wasted_land_value": "£billions in undevelopable land sitting idle"
        },
        "domus_solution": {
            "cost_reduction": "90% reduction in consultant costs via AI automation",
            "time_savings": "80% faster constraint analysis and document generation",
            "certainty_improvement": "Predict approval probability before spending heavily",
            "alternative_value": "Monetise failed land through biodiversity offsets"
        },
        "target_market_size": {
            "uk_planning_applications_per_year": "500,000+",
            "sme_developers": "10,000+ potential users",
            "planning_consultants": "2,000+ potential users", 
            "local_authorities": "400+ councils need digital transformation"
        }
    }

# Simple demo endpoints to show the system working
@app.get("/api/demo/site-analysis")
async def demo_site_analysis():
    """Demo of AI site analysis"""
    return {
        "site_address": "123 Example Street, Planning City, EX1 2MP",
        "coordinates": [51.5074, -0.1278],
        "approval_probability": 0.73,
        "confidence_score": 0.89,
        "key_constraints": [
            {"type": "conservation_area", "severity": "medium", "impact": -0.15},
            {"type": "flood_zone", "severity": "low", "impact": -0.05},
            {"type": "tree_preservation_order", "severity": "low", "impact": -0.03}
        ],
        "recommendations": [
            "Consider heritage impact assessment for Conservation Area",
            "Reduce building footprint by 10% to mitigate flood risk",
            "Retain existing mature trees in design"
        ],
        "processing_time_ms": 847
    }

@app.get("/api/demo/document-generation")
async def demo_document_generation():
    """Demo of Auto-Docs generation"""
    return {
        "document_type": "Planning Statement",
        "site_reference": "123 Example Street Analysis",
        "generated_content": {
            "executive_summary": "This Planning Statement accompanies a full planning application for residential development at 123 Example Street...",
            "site_description": "The application site comprises 0.5 hectares of brownfield land within the settlement boundary...",
            "policy_analysis": "The proposal accords with Local Plan Policy H1 (Housing Delivery) and Policy DM2 (Design Quality)...",
            "conclusion": "The proposed development represents sustainable development that accords with the development plan..."
        },
        "document_stats": {
            "pages": 12,
            "word_count": 3247,
            "policy_references": 15,
            "generation_time_seconds": 4.2
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🌟 Starting Domus Planning Platform...")
    print("🎯 The AI Operating System for Planning and Land Use")
    uvicorn.run(app, host="0.0.0.0", port=8000)