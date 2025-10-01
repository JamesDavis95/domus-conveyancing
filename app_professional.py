from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import json
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel

app = FastAPI(title="Domus Planning Intelligence Platform")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Pydantic models
class PropertyQuery(BaseModel):
    postcode: str
    property_type: Optional[str] = None

class PlanningPrediction(BaseModel):
    address: str
    development_type: str
    site_area: float
    description: str

class OffsetCredit(BaseModel):
    credit_type: str
    location: str
    units: int
    price_per_unit: float

# Analytics data
def get_personal_analytics():
    return {
        "projects_completed": 12,
        "approval_success_rate": 87,
        "total_cost_savings": 247000,
        "days_saved_total": 156,
        "performance_trends": {
            "accuracy_improvement": 12,
            "prediction_accuracy": 94,
            "risk_assessment_precision": 98.1,
            "generation_speed_improvement": 2.3
        }
    }

def get_market_overview():
    return {
        "total_volume_30d": 4200000,
        "average_credit_price": 287,
        "credits_traded_30d": 14726,
        "active_participants": 342,
        "volume_change": 23,
        "price_change": 4.4,
        "units_change": 1847,
        "participants_change": 18
    }

def get_marketplace_statistics():
    return {
        "price_trends": [
            {"type": "Biodiversity Units", "price": 287, "change": 4.4},
            {"type": "Carbon Credits", "price": 142, "change": 2.1},
            {"type": "Water Quality Units", "price": 195, "change": -1.2},
            {"type": "Habitat Credits", "price": 324, "change": 7.8}
        ],
        "regional_activity": [
            {"region": "East Hertfordshire", "volume": 1247, "value": 357000},
            {"region": "Central Bedfordshire", "volume": 892, "value": 256000},
            {"region": "North Essex", "volume": 634, "value": 182000},
            {"region": "Surrey Heath", "volume": 523, "value": 169000}
        ],
        "trading_volumes": {
            "today": {"units": 127, "value": 36500},
            "week": {"units": 1043, "value": 299000},
            "month": {"units": 4726, "value": 1350000},
            "year": {"units": 23847, "value": 6840000}
        }
    }

def get_api_usage():
    return {
        "api_calls_month": {
            "used": 2847,
            "limit": 10000,
            "percentage": 28
        },
        "rate_limit": {
            "current": 27,
            "limit": 60,
            "percentage": 45
        },
        "active_keys": {
            "used": 3,
            "limit": 5
        }
    }

def get_available_endpoints():
    return [
        {
            "method": "GET",
            "path": "/api/v1/property/{postcode}",
            "status": "active",
            "description": "Retrieve comprehensive property data for a given postcode including planning history, property details, and local area information.",
            "calls_30d": 1247,
            "avg_response": "250ms",
            "success_rate": 99.8
        },
        {
            "method": "GET", 
            "path": "/api/v1/planning/applications",
            "status": "active",
            "description": "Search and filter planning applications by location, date range, status, and application type.",
            "calls_30d": 892,
            "avg_response": "180ms",
            "success_rate": 99.9
        },
        {
            "method": "POST",
            "path": "/api/v1/analysis/predict",
            "status": "active", 
            "description": "Submit property details for AI-powered planning approval prediction and risk assessment.",
            "calls_30d": 456,
            "avg_response": "2.3s",
            "success_rate": 98.7
        },
        {
            "method": "GET",
            "path": "/api/v1/offsets/marketplace",
            "status": "beta",
            "description": "Access environmental offset marketplace data including available credits, pricing, and trading activity.",
            "calls_30d": 234,
            "avg_response": "320ms", 
            "success_rate": 97.4
        }
    ]

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the platform homepage."""
    return FileResponse("frontend/platform_new.html", headers={"Cache-Control": "no-cache"})

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "active_projects": 24,
        "api_requests": 8247,
        "documents_generated": 156,
        "offsets_trading": 12340,
        "in_progress": 18,
        "review_stage": 6,
        "api_today": 342,
        "api_remaining": 1753,
        "docs_this_month": 42,
        "success_rate": 98.4,
        "units_traded": 47,
        "avg_price": 262
    }

@app.get("/api/dashboard/analytics")
async def get_dashboard_analytics():
    return get_personal_analytics()

@app.get("/api/projects")
async def get_projects():
    return [
        {
            "id": 1,
            "name": "Riverside Residential Development",
            "status": "approved",
            "submitted": "2 weeks ago",
            "predicted_odds": 89,
            "cost_saved": 18500,
            "decision_time": "8 days early"
        },
        {
            "id": 2,
            "name": "Commercial Office Extension", 
            "status": "in-review",
            "submitted": "5 days ago",
            "predicted_odds": 76,
            "recommendation": "Minor amendments needed",
            "expected_decision": "12 days"
        },
        {
            "id": 3,
            "name": "Mixed-Use Development Analysis",
            "status": "draft",
            "submitted": "Yesterday",
            "predicted_odds": 82,
            "current_status": "Gathering documents",
            "next_step": "AI risk analysis"
        }
    ]

@app.get("/api/marketplace/overview")
async def get_marketplace_overview():
    return get_market_overview()

@app.get("/api/marketplace/statistics")
async def get_marketplace_stats():
    return get_marketplace_statistics()

@app.get("/api/marketplace/credits")
async def get_available_credits():
    return [
        {
            "type": "Biodiversity Units",
            "location": "Hertfordshire, AL3 8QE",
            "units_available": 47,
            "price_per_unit": 284,
            "rating": "AAA",
            "icon": "🌿"
        },
        {
            "type": "Habitat Credits",
            "location": "Bedfordshire, MK45 2DA", 
            "units_available": 23,
            "price_per_unit": 327,
            "rating": "AA",
            "icon": "🏞️"
        },
        {
            "type": "Carbon Credits",
            "location": "Essex, CO6 3HB",
            "units_available": 156,
            "price_per_unit": 145,
            "rating": "A", 
            "icon": "🌱"
        },
        {
            "type": "Water Quality Units",
            "location": "Surrey, GU15 3YL",
            "units_available": 89,
            "price_per_unit": 198,
            "rating": "AA",
            "icon": "💧"
        }
    ]

@app.get("/api/marketplace/portfolio")
async def get_portfolio():
    return [
        {
            "type": "Biodiversity Units",
            "units_owned": 23,
            "current_value": 6670,
            "avg_purchase_price": 278,
            "current_market_price": 287,
            "gain": 207,
            "gain_percentage": 3.2,
            "icon": "🌿"
        },
        {
            "type": "Habitat Credits",
            "units_owned": 15,
            "current_value": 4860,
            "avg_purchase_price": 298,
            "current_market_price": 324,
            "gain": 390,
            "gain_percentage": 8.7,
            "icon": "🏞️"
        },
        {
            "type": "Carbon Credits",
            "units_owned": 342,
            "current_value": 48564,
            "avg_purchase_price": 138,
            "current_market_price": 142,
            "gain": 1368,
            "gain_percentage": 2.9,
            "icon": "🌱"
        }
    ]

@app.get("/api/property/{postcode}")
async def get_property_data(postcode: str):
    return {
        "status": "success",
        "data": {
            "postcode": postcode,
            "properties": [
                {
                    "address": f"123 High Street, {postcode.split()[0]}",
                    "uprn": "10012345678",
                    "property_type": "Terraced House",
                    "planning_applications": 3,
                    "last_application": "2024-08-15",
                    "approval_rate": 0.87
                }
            ],
            "area_stats": {
                "avg_approval_rate": 0.73,
                "total_applications": 1247,
                "avg_decision_time": "8.3 weeks"
            }
        }
    }

@app.post("/api/analysis/predict")
async def predict_planning_approval(prediction: PlanningPrediction):
    # Simulate AI analysis
    approval_probability = 0.76 if "extension" in prediction.description.lower() else 0.82
    
    return {
        "status": "success",
        "prediction": {
            "approval_probability": approval_probability,
            "confidence": 0.94,
            "risk_factors": [
                "Height restrictions in conservation area",
                "Neighbor consultation required"
            ],
            "recommendations": [
                "Submit heritage statement",
                "Consider reducing proposed height by 0.5m"
            ],
            "estimated_timeline": "10-12 weeks",
            "cost_estimate": {
                "application_fee": 462,
                "consultant_costs": 2800,
                "total": 3262
            }
        }
    }

@app.get("/api/api-management/usage")
async def get_api_usage_stats():
    return get_api_usage()

@app.get("/api/api-management/endpoints")
async def get_api_endpoints():
    return get_available_endpoints()

@app.get("/api/api-management/keys")
async def get_api_keys():
    return [
        {
            "id": "pk_live_5a2b",
            "name": "Production API Key",
            "key_preview": "pk_live_••••••••••••••••••••••••5a2b",
            "created": "Aug 15, 2025",
            "calls_this_month": 2847,
            "last_used": "2 hours ago"
        },
        {
            "id": "pk_test_9c1d",
            "name": "Development API Key", 
            "key_preview": "pk_test_••••••••••••••••••••••••9c1d",
            "created": "Jul 22, 2025",
            "calls_this_month": 156,
            "last_used": "3 days ago"
        },
        {
            "id": "pk_live_7f8e",
            "name": "Legacy Integration Key",
            "key_preview": "pk_live_••••••••••••••••••••••••7f8e",
            "created": "Jun 10, 2025",
            "calls_this_month": 0,
            "last_used": "Never"
        }
    ]

@app.post("/api/offsets/buy")
async def buy_offset_credits(credit: OffsetCredit):
    total_cost = credit.units * credit.price_per_unit
    return {
        "status": "success",
        "transaction_id": "txn_abc123def456",
        "credit_type": credit.credit_type,
        "units_purchased": credit.units,
        "price_per_unit": credit.price_per_unit,
        "total_cost": total_cost,
        "estimated_delivery": "2-3 business days"
    }

@app.get("/api/billing/usage")
async def get_billing_usage():
    return {
        "plan": "Professional",
        "billing_cycle": "Sep 1 - Sep 30, 2025",
        "usage": [
            {
                "service": "Document Generations",
                "used": 342,
                "limit": 500,
                "percentage": 68,
                "reset_date": "Sep 30, 2025"
            },
            {
                "service": "API Calls",
                "used": 2847,
                "limit": 10000, 
                "percentage": 28,
                "reset_date": "Sep 30, 2025"
            },
            {
                "service": "Team Members",
                "used": 12,
                "limit": 15,
                "percentage": 80,
                "reset_date": "Upgrade required"
            }
        ]
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)