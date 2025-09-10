#!/usr/bin/env bash
set -euo pipefail

: "${S3_ENDPOINT:=http://localhost:9000}"
: "${OLD_ACCESS_KEY:?Set OLD_ACCESS_KEY}"
: "${OLD_SECRET_KEY:?Set OLD_SECRET_KEY}"
: "${NEW_ACCESS_KEY:?Set NEW_ACCESS_KEY}"
: "${NEW_SECRET_KEY:?Set NEW_SECRET_KEY}"

echo "Rotating MinIO keys at ${S3_ENDPOINT}..."

mc alias set domus "${S3_ENDPOINT}" "${OLD_ACCESS_KEY}" "${OLD_SECRET_KEY}"
mc admin user add domus "${NEW_ACCESS_KEY}" "${NEW_SECRET_KEY}" || true
mc admin policy set domus readwrite user="${NEW_ACCESS_KEY}"

echo "Update your .env and docker-compose with new keys, then restart services."
