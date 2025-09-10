#!/usr/bin/env bash
set -euo pipefail

echo ">> Scanning and fixing settings references..."

# Pairs of old=new
PAIRS=(
  "settings.REDIS_URL=settings.REDIS_URL"
  "settings.DATABASE_URL=settings.DATABASE_URL"
  "settings.S3_ENDPOINT=settings.S3_ENDPOINT"
  "settings.S3_ACCESS_KEY=settings.S3_ACCESS_KEY"
  "settings.S3_SECRET_KEY=settings.S3_SECRET_KEY"
  "settings.S3_BUCKET=settings.S3_BUCKET"
  "settings.CLAMAV_HOST=settings.CLAMAV_HOST"
  "settings.CLAMAV_PORT=settings.CLAMAV_PORT"
  "settings.AUTH_ENABLED=settings.AUTH_ENABLED"
  "settings.OIDC_AUTHORITY=settings.OIDC_AUTHORITY"
  "settings.OIDC_CLIENT_ID=settings.OIDC_CLIENT_ID"
  "settings.OIDC_CLIENT_SECRET=settings.OIDC_CLIENT_SECRET"
  "settings.OIDC_SCOPE=settings.OIDC_SCOPE"
  "settings.OIDC_REDIRECT_PATH=settings.OIDC_REDIRECT_PATH"
)

for pair in "${PAIRS[@]}"; do
  old="${pair%%=*}"
  new="${pair##*=}"
  echo "Replacing $old -> $new"
  grep -rl "$old" . | while read -r file; do
    sed -i.bak "s/$old/$new/g" "$file"
  done
done

echo ">> Cleanup backup files..."
find . -name "*.bak" -delete

echo ">> Done. Now rebuild your containers:"
echo "   docker-compose build --no-cache api worker"
echo "   docker-compose up -d"
echo "   docker-compose logs --tail=100 api worker"
