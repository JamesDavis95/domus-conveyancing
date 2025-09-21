"""
Public Citizen Portal
Self-Service Applications | Online Payments | Case Tracking | Community Engagement
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from typing import Optional, List
import secrets
import json

# Initialize Citizen Portal API
citizen_api = FastAPI(
    title="Domus Citizen Portal",
    description="Self-Service Planning, Building Control, Licensing & Council Services",
    version="2.0.0"
)

# ============================================================================
# PUBLIC APPLICATION SUBMISSION PORTAL
# ============================================================================

@citizen_api.get("/", response_class=HTMLResponse)
async def citizen_portal_home():
    """Main citizen portal homepage"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Council Services Portal</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }
            .header { background: linear-gradient(135deg, #2c5aa0 0%, #1e3a66 100%); color: white; padding: 2rem 0; }
            .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
            .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
            .header p { font-size: 1.2rem; opacity: 0.9; }
            
            .services-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; padding: 3rem 0; }
            .service-card { 
                background: white; 
                border-radius: 12px; 
                box-shadow: 0 4px 20px rgba(0,0,0,0.1); 
                overflow: hidden; 
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .service-card:hover { transform: translateY(-5px); box-shadow: 0 8px 30px rgba(0,0,0,0.15); }
            .card-header { background: #f8f9fa; padding: 1.5rem; border-bottom: 1px solid #e9ecef; }
            .card-header h3 { color: #2c5aa0; font-size: 1.4rem; margin-bottom: 0.5rem; }
            .card-body { padding: 1.5rem; }
            .service-features { list-style: none; margin-bottom: 1.5rem; }
            .service-features li { padding: 0.5rem 0; border-bottom: 1px solid #f0f0f0; }
            .service-features li:before { content: "✓"; color: #28a745; font-weight: bold; margin-right: 10px; }
            
            .cta-button { 
                display: inline-block; 
                background: #2c5aa0; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 6px; 
                font-weight: 600;
                transition: background 0.3s ease;
            }
            .cta-button:hover { background: #1e3a66; }
            
            .stats-section { background: #f8f9fa; padding: 3rem 0; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; text-align: center; }
            .stat-item h4 { font-size: 2.5rem; color: #2c5aa0; margin-bottom: 0.5rem; }
            .stat-item p { color: #666; }
            
            .footer { background: #2c5aa0; color: white; padding: 2rem 0; text-align: center; }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <h1>Council Services Portal</h1>
                <p>Apply online, track your applications, and access council services 24/7</p>
            </div>
        </header>
        
        <main>
            <section class="container">
                <div class="services-grid">
                    <div class="service-card">
                        <div class="card-header">
                            <h3>🏠 Planning Applications</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Submit planning applications online</li>
                                <li>Upload documents and plans</li>
                                <li>Track application progress</li>
                                <li>View consultation responses</li>
                                <li>Make payments securely</li>
                            </ul>
                            <a href="/citizen/planning" class="cta-button">Apply for Planning Permission</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="card-header">
                            <h3>🏗️ Building Control</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Building regulations applications</li>
                                <li>Schedule site inspections</li>
                                <li>Download completion certificates</li>
                                <li>Safety compliance guidance</li>
                                <li>Fast-track processing available</li>
                            </ul>
                            <a href="/citizen/building-control" class="cta-button">Submit Building Control</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="card-header">
                            <h3>🗂️ Land Charges</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Official local land charges searches</li>
                                <li>Instant digital certificates</li>
                                <li>Property development info</li>
                                <li>Environmental data included</li>
                                <li>Legal protection guarantee</li>
                            </ul>
                            <a href="/citizen/land-charges" class="cta-button">Order Land Charge Search</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="card-header">
                            <h3>♻️ Waste & Licensing</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Waste carrier registration</li>
                                <li>Environmental permits</li>
                                <li>Business licensing</li>
                                <li>Compliance monitoring</li>
                                <li>Renewal reminders</li>
                            </ul>
                            <a href="/citizen/waste-licensing" class="cta-button">Apply for License</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="card-header">
                            <h3>🏡 Housing Standards</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Report housing conditions</li>
                                <li>HMO license applications</li>
                                <li>Energy efficiency advice</li>
                                <li>Tenant rights information</li>
                                <li>Landlord compliance checks</li>
                            </ul>
                            <a href="/citizen/housing" class="cta-button">Housing Services</a>
                        </div>
                    </div>
                    
                    <div class="service-card">
                        <div class="card-header">
                            <h3>📋 My Applications</h3>
                        </div>
                        <div class="card-body">
                            <ul class="service-features">
                                <li>Track all your applications</li>
                                <li>Receive status updates</li>
                                <li>Access decision notices</li>
                                <li>Download certificates</li>
                                <li>Make additional payments</li>
                            </ul>
                            <a href="/citizen/my-applications" class="cta-button">View My Applications</a>
                        </div>
                    </div>
                </div>
            </section>
            
            <section class="stats-section">
                <div class="container">
                    <div class="stats-grid">
                        <div class="stat-item">
                            <h4>78%</h4>
                            <p>Applications Submitted Online</p>
                        </div>
                        <div class="stat-item">
                            <h4>42</h4>
                            <p>Days Average Processing</p>
                        </div>
                        <div class="stat-item">
                            <h4>96%</h4>
                            <p>Customer Satisfaction</p>
                        </div>
                        <div class="stat-item">
                            <h4>24/7</h4>
                            <p>Online Service Availability</p>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        
        <footer class="footer">
            <div class="container">
                <p>&copy; 2025 Council Services Portal. Powered by Domus Platform Technology.</p>
            </div>
        </footer>
    </body>
    </html>
    """

# ============================================================================
# PLANNING APPLICATION PORTAL
# ============================================================================

@citizen_api.get("/citizen/planning", response_class=HTMLResponse)
async def planning_application_portal():
    """Planning application submission portal"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Planning Application Portal</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }
            .header { background: #2c5aa0; color: white; padding: 1rem 0; }
            .container { max-width: 800px; margin: 0 auto; padding: 0 20px; }
            .form-container { background: white; margin: 2rem auto; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            
            .form-section { margin-bottom: 2rem; }
            .form-section h3 { color: #2c5aa0; margin-bottom: 1rem; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #333; }
            .form-group input, .form-group select, .form-group textarea { 
                width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 1rem; 
            }
            .form-group textarea { height: 120px; resize: vertical; }
            
            .file-upload { 
                border: 2px dashed #ddd; padding: 2rem; text-align: center; border-radius: 8px; 
                background: #fafafa; transition: all 0.3s ease;
            }
            .file-upload:hover { border-color: #2c5aa0; background: #f0f4ff; }
            .file-upload input[type="file"] { margin: 1rem 0; }
            
            .fee-calculator { background: #e8f4f8; padding: 1.5rem; border-radius: 8px; margin: 1rem 0; }
            .fee-display { font-size: 1.5rem; font-weight: bold; color: #2c5aa0; text-align: center; }
            
            .submit-button { 
                background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 6px; 
                font-size: 1.1rem; font-weight: 600; cursor: pointer; width: 100%;
            }
            .submit-button:hover { background: #218838; }
            
            .progress-indicator { display: flex; justify-content: space-between; margin-bottom: 2rem; }
            .progress-step { flex: 1; text-align: center; padding: 1rem; background: #f8f9fa; margin: 0 0.5rem; border-radius: 6px; }
            .progress-step.active { background: #2c5aa0; color: white; }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <h1>Planning Application Portal</h1>
                <p>Submit your planning application quickly and securely online</p>
            </div>
        </header>
        
        <main class="container">
            <div class="form-container">
                <div class="progress-indicator">
                    <div class="progress-step active">1. Application Details</div>
                    <div class="progress-step">2. Site Information</div>
                    <div class="progress-step">3. Documents</div>
                    <div class="progress-step">4. Payment</div>
                </div>
                
                <form id="planningForm">
                    <div class="form-section">
                        <h3>Application Type</h3>
                        <div class="form-group">
                            <label for="applicationType">Type of Application</label>
                            <select id="applicationType" onchange="calculateFee()">
                                <option value="">Select Application Type</option>
                                <option value="householder">Householder Development (£206)</option>
                                <option value="minor">Minor Development (£462)</option>
                                <option value="major">Major Development (£924)</option>
                                <option value="change_of_use">Change of Use (£462)</option>
                                <option value="listed_building">Listed Building Consent (£206)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="description">Development Description</label>
                            <textarea id="description" placeholder="Describe your proposed development in detail..."></textarea>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3>Site Information</h3>
                        <div class="form-group">
                            <label for="siteAddress">Site Address</label>
                            <textarea id="siteAddress" placeholder="Enter the full address of the development site..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="landOwnership">Land Ownership</label>
                            <select id="landOwnership">
                                <option value="owned">I own the land</option>
                                <option value="part_owned">I own part of the land</option>
                                <option value="not_owned">I do not own the land</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3>Applicant Details</h3>
                        <div class="form-group">
                            <label for="applicantName">Full Name</label>
                            <input type="text" id="applicantName" placeholder="Enter your full name">
                        </div>
                        
                        <div class="form-group">
                            <label for="applicantAddress">Address</label>
                            <textarea id="applicantAddress" placeholder="Enter your address..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="phone">Phone Number</label>
                            <input type="tel" id="phone" placeholder="Enter your phone number">
                        </div>
                        
                        <div class="form-group">
                            <label for="email">Email Address</label>
                            <input type="email" id="email" placeholder="Enter your email address">
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3>Required Documents</h3>
                        <div class="file-upload">
                            <h4>Upload Planning Documents</h4>
                            <p>Required: Site plan, floor plans, elevations (PDF, max 10MB each)</p>
                            <input type="file" id="planningDocs" multiple accept=".pdf,.jpg,.png">
                            <p><small>Drag and drop files here or click to browse</small></p>
                        </div>
                    </div>
                    
                    <div class="form-section">
                        <h3>Application Fee</h3>
                        <div class="fee-calculator">
                            <div class="fee-display" id="feeDisplay">£0.00</div>
                            <p>Application fee (includes statutory consultation)</p>
                        </div>
                    </div>
                    
                    <button type="submit" class="submit-button">Submit Application & Pay</button>
                </form>
            </div>
        </main>
        
        <script>
            function calculateFee() {
                const appType = document.getElementById('applicationType').value;
                const feeDisplay = document.getElementById('feeDisplay');
                
                const fees = {
                    'householder': 206,
                    'minor': 462,
                    'major': 924,
                    'change_of_use': 462,
                    'listed_building': 206
                };
                
                const fee = fees[appType] || 0;
                feeDisplay.textContent = `£${fee.toFixed(2)}`;
            }
            
            document.getElementById('planningForm').addEventListener('submit', function(e) {
                e.preventDefault();
                alert('Application submitted successfully! Reference: PLAN/2025/' + Math.floor(Math.random() * 10000));
            });
        </script>
    </body>
    </html>
    """

# ============================================================================
# APPLICATION TRACKING PORTAL
# ============================================================================

@citizen_api.get("/citizen/my-applications", response_class=HTMLResponse)
async def application_tracking_portal():
    """Application tracking and status portal"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>My Applications - Track Progress</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; }
            .header { background: #2c5aa0; color: white; padding: 1rem 0; }
            .container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
            
            .dashboard { background: white; margin: 2rem auto; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
            .stat-card { background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center; border-left: 4px solid #2c5aa0; }
            .stat-number { font-size: 2rem; font-weight: bold; color: #2c5aa0; }
            .stat-label { color: #666; font-size: 0.9rem; }
            
            .applications-list { margin-top: 2rem; }
            .application-item { 
                background: white; border: 1px solid #e9ecef; margin-bottom: 1rem; 
                border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .app-header { 
                background: #f8f9fa; padding: 1rem 1.5rem; display: flex; 
                justify-content: space-between; align-items: center; border-bottom: 1px solid #e9ecef;
            }
            .app-reference { font-weight: bold; color: #2c5aa0; }
            .app-status { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.875rem; font-weight: 600; }
            .status-submitted { background: #cce7ff; color: #0066cc; }
            .status-under-review { background: #fff3cd; color: #856404; }
            .status-approved { background: #d4edda; color: #155724; }
            .status-decided { background: #d1ecf1; color: #0c5460; }
            
            .app-body { padding: 1.5rem; }
            .app-details { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
            .detail-item { }
            .detail-label { font-weight: 600; color: #666; font-size: 0.875rem; }
            .detail-value { color: #333; }
            
            .progress-bar { background: #e9ecef; height: 8px; border-radius: 4px; overflow: hidden; margin: 1rem 0; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #2c5aa0, #4169E1); transition: width 0.3s ease; }
            
            .action-buttons { display: flex; gap: 1rem; margin-top: 1rem; }
            .btn { 
                padding: 0.5rem 1rem; border: none; border-radius: 4px; 
                cursor: pointer; font-size: 0.875rem; text-decoration: none; display: inline-block;
            }
            .btn-primary { background: #2c5aa0; color: white; }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-success { background: #28a745; color: white; }
        </style>
    </head>
    <body>
        <header class="header">
            <div class="container">
                <h1>My Applications Dashboard</h1>
                <p>Track the progress of all your applications in real-time</p>
            </div>
        </header>
        
        <main class="container">
            <div class="dashboard">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">7</div>
                        <div class="stat-label">Total Applications</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">3</div>
                        <div class="stat-label">Under Review</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">2</div>
                        <div class="stat-label">Approved</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">38</div>
                        <div class="stat-label">Days Avg Processing</div>
                    </div>
                </div>
                
                <div class="applications-list">
                    <h3 style="margin-bottom: 1rem; color: #2c5aa0;">Recent Applications</h3>
                    
                    <div class="application-item">
                        <div class="app-header">
                            <span class="app-reference">PLAN/2025/0847</span>
                            <span class="app-status status-under-review">Under Review</span>
                        </div>
                        <div class="app-body">
                            <h4>Single storey rear extension</h4>
                            <div class="app-details">
                                <div class="detail-item">
                                    <div class="detail-label">Property</div>
                                    <div class="detail-value">15 Oak Avenue, Anytown</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Submitted</div>
                                    <div class="detail-value">12 August 2025</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Officer</div>
                                    <div class="detail-value">Sarah Johnson</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Target Decision</div>
                                    <div class="detail-value">7 October 2025</div>
                                </div>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 65%;"></div>
                            </div>
                            <p><small>Progress: Consultation period completed, officer assessment in progress</small></p>
                            <div class="action-buttons">
                                <a href="#" class="btn btn-primary">View Details</a>
                                <a href="#" class="btn btn-secondary">Download Documents</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="application-item">
                        <div class="app-header">
                            <span class="app-reference">BC/2025/0234</span>
                            <span class="app-status status-approved">Approved</span>
                        </div>
                        <div class="app-body">
                            <h4>Building regulations - Loft conversion</h4>
                            <div class="app-details">
                                <div class="detail-item">
                                    <div class="detail-label">Property</div>
                                    <div class="detail-value">22 Elm Street, Anytown</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Approved</div>
                                    <div class="detail-value">28 July 2025</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Inspector</div>
                                    <div class="detail-value">Mike Peters</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Completion Certificate</div>
                                    <div class="detail-value">Available</div>
                                </div>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 100%;"></div>
                            </div>
                            <p><small>All inspections passed, completion certificate issued</small></p>
                            <div class="action-buttons">
                                <a href="#" class="btn btn-success">Download Certificate</a>
                                <a href="#" class="btn btn-primary">View Inspection Reports</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="application-item">
                        <div class="app-header">
                            <span class="app-reference">LLC/2025/1456</span>
                            <span class="app-status status-decided">Completed</span>
                        </div>
                        <div class="app-body">
                            <h4>Local Land Charges Search</h4>
                            <div class="app-details">
                                <div class="detail-item">
                                    <div class="detail-label">Property</div>
                                    <div class="detail-value">8 Pine Close, Anytown</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Completed</div>
                                    <div class="detail-value">15 September 2025</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Charges Found</div>
                                    <div class="detail-value">None</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Certificate Valid</div>
                                    <div class="detail-value">Until 15 Sept 2031</div>
                                </div>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: 100%;"></div>
                            </div>
                            <p><small>Search completed, official certificate available for download</small></p>
                            <div class="action-buttons">
                                <a href="#" class="btn btn-success">Download Certificate</a>
                                <a href="#" class="btn btn-primary">Order Additional Searches</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </body>
    </html>
    """

# ============================================================================
# CITIZEN API ENDPOINTS
# ============================================================================

@citizen_api.post("/api/citizen/planning/submit")
async def submit_planning_application(application_data: dict):
    """Submit planning application from citizen portal"""
    application_ref = f"PLAN/2025/{secrets.randbelow(9999):04d}"
    
    return {
        "success": True,
        "application_reference": application_ref,
        "submitted_date": datetime.now().isoformat(),
        "target_decision_date": (datetime.now() + timedelta(weeks=8)).strftime("%Y-%m-%d"),
        "fee_paid": application_data.get("fee", 462),
        "next_steps": [
            "Application validated within 5 working days",
            "Consultation period (21 days)",
            "Officer assessment",
            "Decision notice issued"
        ],
        "tracking_url": f"/citizen/track/{application_ref}",
        "contact_email": "planning@council.gov.uk"
    }

@citizen_api.get("/api/citizen/applications/{user_id}")
async def get_user_applications(user_id: str):
    """Get all applications for a user"""
    return {
        "user_id": user_id,
        "applications": [
            {
                "reference": "PLAN/2025/0847",
                "type": "Planning Application",
                "description": "Single storey rear extension",
                "status": "Under Review",
                "progress": 65,
                "submitted": "2025-08-12",
                "target_decision": "2025-10-07",
                "officer": "Sarah Johnson"
            },
            {
                "reference": "BC/2025/0234", 
                "type": "Building Control",
                "description": "Loft conversion",
                "status": "Approved",
                "progress": 100,
                "approved": "2025-07-28",
                "inspector": "Mike Peters"
            },
            {
                "reference": "LLC/2025/1456",
                "type": "Land Charges Search",
                "description": "Property purchase search",
                "status": "Completed",
                "progress": 100,
                "completed": "2025-09-15"
            }
        ],
        "summary": {
            "total_applications": 7,
            "under_review": 3,
            "approved": 2,
            "completed": 2,
            "average_processing_days": 38
        }
    }

@citizen_api.post("/api/citizen/payment/process")
async def process_citizen_payment(payment_data: dict):
    """Process payment for citizen applications"""
    payment_ref = f"PAY{datetime.now().strftime('%Y%m%d')}{secrets.randbelow(9999):04d}"
    
    return {
        "payment_successful": True,
        "payment_reference": payment_ref,
        "amount": payment_data.get("amount", 462.00),
        "method": payment_data.get("method", "card"),
        "transaction_id": f"TXN{secrets.randbelow(999999):06d}",
        "receipt_url": f"/citizen/receipt/{payment_ref}",
        "application_reference": payment_data.get("application_ref", ""),
        "confirmation": "Payment processed successfully - application will now proceed to validation"
    }

@citizen_api.get("/api/citizen/consultations/active")
async def get_active_consultations():
    """Get current planning consultations for public comment"""
    return {
        "active_consultations": [
            {
                "reference": "PLAN/2025/0892",
                "description": "Residential development - 45 new homes",
                "location": "Land off Church Lane",
                "consultation_start": "2025-09-01",
                "consultation_end": "2025-09-22",
                "days_remaining": 7,
                "comments_received": 23,
                "view_url": "/citizen/consultation/PLAN-2025-0892"
            },
            {
                "reference": "PLAN/2025/0903", 
                "description": "Change of use - Shop to residential",
                "location": "12 High Street",
                "consultation_start": "2025-09-08",
                "consultation_end": "2025-09-29",
                "days_remaining": 14,
                "comments_received": 8,
                "view_url": "/citizen/consultation/PLAN-2025-0903"
            }
        ],
        "consultation_info": {
            "how_to_comment": "Comments can be submitted online or by email",
            "comment_deadline": "5pm on the consultation end date",
            "contact_email": "planning.consultation@council.gov.uk"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(citizen_api, host="0.0.0.0", port=8004)