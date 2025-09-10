# Domus Conveyancing API

A FastAPI-based service for conveyancing document processing and risk assessment.

## Quickstart

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for full stack)

### Local Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repo-url>
   cd domus-conveyancing
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the service:**
   ```bash
   # Option 1: Simple start (SQLite, minimal dependencies)
   export DATABASE_URL="sqlite:///./app.db"
   python -m uvicorn main:app --reload --port 8000
   
   # Option 2: Full stack with Docker Compose
   docker-compose up -d
   ```

### Smoke Tests

Once the service is running, validate it works with these curl commands:

```bash
# Health checks
curl -f http://localhost:8000/health
curl -f http://localhost:8000/ready
curl -f http://localhost:8000/metrics

# API functionality  
curl -X POST http://localhost:8000/api/matters \
  -H "Content-Type: application/json" \
  -d '{}'

# List matters
curl http://localhost:8000/la/matters/list

# Get matter details (replace {id} with actual matter ID from above)
curl http://localhost:8000/api/matters/{id}
```

### Expected Responses

- **Health**: `{"ok": true, "env": "dev"}`
- **Ready**: `{"ok": true, ...}` (with service status details)
- **Metrics**: Prometheus-format metrics
- **Create Matter**: `{"matter": {"id": 1, "ref": "AUTO"}}`
- **List Matters**: `{"matters": [{"id": 1, "ref": "AUTO", ...}]}`

### Configuration

Key environment variables:

- `DATABASE_URL`: Database connection (defaults to SQLite for Codespaces)
- `REDIS_URL`: Redis connection for caching
- `APP_ENV`: Environment name (dev/prod)
- `PROMETHEUS_MULTIPROC_DIR`: Enable multiprocess metrics (optional)

### API Endpoints

- `GET /health` - Health check
- `GET /ready` - Readiness probe
- `GET /metrics` - Prometheus metrics
- `POST /api/matters` - Create new matter
- `GET /api/matters/{id}` - Get matter details
- `GET /la/matters/list` - List all matters
- `POST /matters/{id}/upload` - Upload PDF document
- `POST /matters/{id}/risk-scan` - Run risk assessment

## Development

### Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/
```

### Docker Development

```bash
# Build and run
docker-compose up --build

# View logs
docker-compose logs -f api

# Shell into container
docker-compose exec api bash
```

### Contributing

1. Make changes following minimal-change principles
2. Test locally with the smoke tests above
3. Submit PR with clear description

For issues or questions, please open a GitHub issue.