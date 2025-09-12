#!/usr/bin/env python3
import os
import subprocess
import sys

# Get the port from environment variable, default to 8000
port = os.environ.get('PORT', '8000')

# Make sure port is a valid integer
try:
    port_int = int(port)
except ValueError:
    port_int = 8000

# Run uvicorn with the correct port
cmd = [
    sys.executable, '-m', 'uvicorn', 
    'app_secured:app', 
    '--host', '0.0.0.0', 
    '--port', str(port_int)
]

print(f"Starting server on port {port_int}")
subprocess.run(cmd)