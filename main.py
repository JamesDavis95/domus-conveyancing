"""
Domus Planning Platform - Production Entry Point
Full platform with all integrations
"""

import os
from pathlib import Path

# Load environment variables for production
def load_environment():
    """Load environment variables from .env.production"""
    env_file = Path(__file__).parent / '.env.production'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment first
load_environment()

# Import the full app with all integrations
from app import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)