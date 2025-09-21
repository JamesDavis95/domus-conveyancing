# Domus Planning Platform

**AI-Powered Integrated Planning Services for Local Authorities**

An integrated platform supporting Planning Applications, Building Control, Land Charges, and Regulatory Services with automated policy compliance checking and intelligent decision support.

## 🎯 **Key Features**

### **Planning Applications**
- Automated policy compliance checking against local development plans
- AI-powered application analysis and risk assessment
- Streamlined officer decision workflows
- Public consultation management

### **Integrated Services**
- **Building Control**: Application processing and inspection scheduling
- **Land Charges**: LLC1 searches and charge management  
- **Waste Licensing**: Regulatory compliance and permit tracking
- **Housing Standards**: HMO licensing and enforcement

### **AI & Automation**
- Document parsing and data extraction
- Policy rule engine with compliance scoring
- Predictive processing timelines
- Automated risk flagging and recommendations

## 🚀 **Quick Start**

```bash
# Set up authentication (optional)
export AUTH_ENABLED=true
export EXPECTED_API_KEY="demo-key"

# Health check endpoints
curl /health              # Basic health
curl /ready              # Database connectivity  
curl /health/policy      # Policy engine status
```
## OIDC (optional)
Export the following and visit `/login`:
```bash
export OIDC_ENABLED=true
export OIDC_ISSUER="https://login.microsoftonline.com/<tenant-id>/v2.0"
export OIDC_CLIENT_ID="<app-id>"
export OIDC_CLIENT_SECRET="<secret>"
export OIDC_REDIRECT_URI="https://your-host/auth/callback"
export SECRET_KEY="change-me"
```
## SLA & Metrics
`GET /la/metrics/summary` returns:
```json
{ "totals": {"matters": 12, "approved": 7}, "sla": {"avg_seconds_received_to_approved": 86400, "p50_seconds": 72000, "p90_seconds": 129600} }
```

## Jobs (Redis/RQ) — optional
```bash
export REDIS_URL=redis://localhost:6379/0
python worker.py
# UI: use "Async OCR" checkbox; upload enqueues OCR and /api/jobs/{id}/status is polled
```
# Deployment trigger
# Ultra minimal deployment
