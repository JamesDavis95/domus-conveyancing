#!/bin/bash
PORT=${PORT:-8000}
exec uvicorn minimal_working:app --host 0.0.0.0 --port $PORT
