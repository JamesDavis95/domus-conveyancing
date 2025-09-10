#!/usr/bin/env bash
set -euo pipefail

echo ">> Updating worker.py..."
cat > worker.py <<'PY'
import os
import sys
import logging
import rq
from redis import Redis
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("worker")

# ✅ fixed: use REDIS_URL (matches settings.py)
redis = Redis.from_url(settings.REDIS_URL)

# Queue name defaults to "default"
queue = rq.Queue("default", connection=redis)

if __name__ == "__main__":
    logger.info("Starting RQ worker, listening on 'default' queue")
    with rq.Connection(redis):
        worker = rq.Worker([queue])
        worker.work()
PY

echo ">> Ensuring python-jose is in requirements.txt..."
grep -q 'python-jose' requirements.txt || echo 'python-jose[cryptography]' >> requirements.txt

echo ">> Rebuilding containers..."
docker-compose build --no-cache api worker

echo ">> Restarting containers..."
docker-compose up -d

echo ">> Showing logs..."
docker-compose logs --tail=100 api worker
