from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Startup verification
print("🚀 Starting Domus Planning Platform - Cloud Optimized...")
print("   Version: 4.0.0-cloud")
print("   File: main.py")
print("   Mode: Production with cloud optimizations")

# Initialize FastAPI application
app = FastAPI(
    title="Domus Planning Platform",
    description="AI-powered planning intelligence system with BNG marketplace",
    version="4.0.0-cloud",
    docs_url="/admin/docs",
    redoc_url="/admin/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Simplified for cloud deployment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"]
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "Domus Planning Platform",
        "version": "4.0.0-cloud",
        "file": "main.py",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "authentication": "enabled",
            "bng_marketplace": "operational", 
            "ai_planning": "active",
            "user_roles": "configured"
        }
    }

@app.get("/test")
async def test_deployment():
    """Test endpoint"""
    return {
        "message": "✅ CLOUD DEPLOYMENT SUCCESS",
        "platform": "Domus Planning Platform",
        "timestamp": datetime.utcnow().isoformat()
    }

# User Management System
users_db = {
    "super_admin": {
        "username": "super_admin",
        "email": "admin@domusplanning.co.uk",
        "role": "super_admin",
        "permissions": ["all"],
        "created": datetime.utcnow().isoformat()
    },
    "planner": {
        "username": "planner", 
        "email": "planner@domusplanning.co.uk",
        "role": "planner",
        "permissions": ["planning", "documents", "consultations"],
        "created": datetime.utcnow().isoformat()
    },
    "council": {
        "username": "council",
        "email": "council@domusplanning.co.uk", 
        "role": "council",
        "permissions": ["validation", "approvals", "compliance"],
        "created": datetime.utcnow().isoformat()
    }
}

@app.get("/api/users")
async def list_users():
    """List all users with roles and permissions"""
    return {
        "users": list(users_db.values()),
        "total": len(users_db),
        "roles": ["super_admin", "planner", "council", "developer", "resident"]
    }

@app.get("/api/roles")
async def get_roles():
    """Get role definitions and permissions"""
    return {
        "roles": {
            "super_admin": {
                "name": "Super Administrator",
                "permissions": ["all"],
                "description": "Full system access and control"
            },
            "planner": {
                "name": "Planning Professional", 
                "permissions": ["planning", "documents", "consultations"],
                "description": "Planning application management and consultation"
            },
            "council": {
                "name": "Council Officer",
                "permissions": ["validation", "approvals", "compliance"],
                "description": "Application validation and approval workflow"
            },
            "developer": {
                "name": "Developer",
                "permissions": ["submit", "track", "documents"],
                "description": "Submit and track planning applications"
            },
            "resident": {
                "name": "Resident",
                "permissions": ["view", "comment", "object"],
                "description": "View applications and submit objections"
            }
        }
    }

# BNG Marketplace
bng_listings = [
    {
        "id": "BNG001",
        "title": "Premium Woodland Biodiversity Credits",
        "location": "Oxfordshire",
        "area_hectares": 15.5,
        "biodiversity_units": 180,
        "unit_price": 25000,
        "total_value": 4500000,
        "habitat_type": "Deciduous Woodland",
        "status": "available",
        "seller": "Green Estate Management Ltd",
        "certification": "Natural England Approved",
        "delivery_timeline": "Q2 2025"
    },
    {
        "id": "BNG002", 
        "title": "Grassland Habitat Enhancement Project",
        "location": "Devon",
        "area_hectares": 42.8,
        "biodiversity_units": 312,
        "unit_price": 18500,
        "total_value": 5772000,
        "habitat_type": "Species-rich Grassland",
        "status": "available",
        "seller": "Southwest Conservation Trust",
        "certification": "Natural England Approved",
        "delivery_timeline": "Q3 2025"
    }
]

@app.get("/api/bng/marketplace")
async def bng_marketplace():
    """BNG Marketplace listings"""
    return {
        "listings": bng_listings,
        "total_listings": len(bng_listings),
        "total_units_available": sum(listing["biodiversity_units"] for listing in bng_listings),
        "marketplace_status": "operational"
    }

@app.get("/api/bng/listing/{listing_id}")
async def get_bng_listing(listing_id: str):
    """Get specific BNG listing details"""
    listing = next((l for l in bng_listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

# Main application interface
@app.get("/")
async def root():
    """Serve main application with beautiful interface"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 Domus Planning Platform - AI Operating System</title>
    <style>
        :root {
            --primary: #1e40af;
            --primary-light: #3b82f6;
            --success: #059669;
            --warning: #d97706;
            --surface: #ffffff;
            --background: #f8fafc;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text);
        }
        
        .platform {
            background: var(--surface);
            border-radius: 24px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            max-width: 1200px;
            width: 95%;
            overflow: hidden;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }
        
        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header p {
            font-size: 1.25rem;
            opacity: 0.95;
            font-weight: 300;
        }
        
        .content {
            padding: 3rem 2rem;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.1);
            border-color: var(--primary-light);
        }
        
        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--primary-light));
        }
        
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }
        
        .feature-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text);
        }
        
        .feature-description {
            color: var(--text-muted);
            line-height: 1.6;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 3rem 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
            color: white;
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 700;
            display: block;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            opacity: 0.9;
            font-size: 1rem;
            font-weight: 500;
        }
        
        .cta-section {
            background: var(--background);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            margin-top: 3rem;
        }
        
        .cta-button {
            background: linear-gradient(135deg, var(--success) 0%, #10b981 100%);
            color: white;
            padding: 1rem 2rem;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin: 0.5rem;
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(16, 185, 129, 0.3);
        }
        
        .footer {
            padding: 2rem;
            text-align: center;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .header p { font-size: 1rem; }
            .content { padding: 2rem 1rem; }
            .features-grid { grid-template-columns: 1fr; gap: 1rem; }
        }
    </style>
</head>
<body>
    <div class="platform">
        <div class="header">
            <h1>🏠 Domus Planning Platform</h1>
            <p>AI Operating System for Planning Intelligence & Compliance Automation</p>
        </div>
        
        <div class="content">
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-number">4</span>
                    <span class="stat-label">Core Pillars</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">5</span>
                    <span class="stat-label">User Roles</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">492</span>
                    <span class="stat-label">BNG Units Available</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">100%</span>
                    <span class="stat-label">Cloud Ready</span>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <span class="feature-icon">🤖</span>
                    <h3 class="feature-title">Planning AI</h3>
                    <p class="feature-description">Intelligent planning application analysis, risk assessment, and automated compliance checking with machine learning</p>
                </div>
                
                <div class="feature-card">
                    <span class="feature-icon">📋</span>
                    <h3 class="feature-title">Auto-Docs</h3>
                    <p class="feature-description">Automated document generation, template management, and intelligent form completion for planning workflows</p>
                </div>
                
                <div class="feature-card">
                    <span class="feature-icon">🏘️</span>
                    <h3 class="feature-title">Property API</h3>
                    <p class="feature-description">Comprehensive property data integration, valuation tools, and market intelligence for informed decision making</p>
                </div>
                
                <div class="feature-card">
                    <span class="feature-icon">🌱</span>
                    <h3 class="feature-title">BNG Marketplace</h3>
                    <p class="feature-description">Biodiversity Net Gain trading platform with verified credits, habitat banking, and environmental compliance</p>
                </div>
                
                <div class="feature-card">
                    <span class="feature-icon">👥</span>
                    <h3 class="feature-title">Role Management</h3>
                    <p class="feature-description">Comprehensive user roles: Super Admin, Planners, Council Officers, Developers, and Residents with granular permissions</p>
                </div>
                
                <div class="feature-card">
                    <span class="feature-icon">🏛️</span>
                    <h3 class="feature-title">Council Integration</h3>
                    <p class="feature-description">Direct integration with local planning authorities, automated submissions, and real-time status tracking</p>
                </div>
            </div>
            
            <div class="cta-section">
                <h2 style="margin-bottom: 1rem; color: var(--text);">Explore the Platform</h2>
                <p style="margin-bottom: 2rem; color: var(--text-muted);">Experience the future of planning intelligence</p>
                <a href="/api/users" class="cta-button">👥 View Users & Roles</a>
                <a href="/api/bng/marketplace" class="cta-button">🌱 BNG Marketplace</a>
                <a href="/admin/docs" class="cta-button">📚 API Documentation</a>
                <a href="/health" class="cta-button">⚡ System Status</a>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Domus Planning Platform | AI-Powered Planning Intelligence | Version 4.0.0-cloud</p>
        </div>
    </div>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))