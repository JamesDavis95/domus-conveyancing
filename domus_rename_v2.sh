#!/usr/bin/env bash
set -euo pipefail

echo ">> Fixing settings references (round 2)..."

PAIRS=(
  "settings.REDIS_URL=settings.REDIS_URL"
  "settings.DATABASE_URL=settings.DATABASE_URL"
  "settings.S3_ENDPOINT=settings.S3_ENDPOINT"
  "settings.S3_ACCESS_KEY=settings.S3_ACCESS_KEY"
  "settings.S3_SECRET_KEY=settings.S3_SECRET_KEY"
  "settings.S3_BUCKET=settings.S3_BUCKET"
  "settings.S3_REGION=settings.S3_REGION"
  "settings.S3_PATH_STYLE=settings.S3_PATH_STYLE"
  "settings.AV_SCAN=settings.AV_SCAN"
  "settings.CLAMAV_HOST=settings.CLAMAV_HOST"
  "settings.CLAMAV_PORT=settings.CLAMAV_PORT"
  "settings.AUTH_ENABLED=settings.AUTH_ENABLED"
  "settings.OIDC_AUTHORITY=settings.OIDC_AUTHORITY"
  "settings.OIDC_CLIENT_ID=settings.OIDC_CLIENT_ID"
  "settings.OIDC_CLIENT_SECRET=settings.OIDC_CLIENT_SECRET"
  "settings.OIDC_SCOPE=settings.OIDC_SCOPE"
  "settings.OIDC_REDIRECT_PATH=settings.OIDC_REDIRECT_PATH"
  "settings.APP_ENV=settings.APP_ENV"
  "settings.SECRET_KEY=settings.SECRET_KEY"
)

for pair in "${PAIRS[@]}"; do
  old="${pair%%=*}"
  new="${pair##*=}"
  echo "Replacing $old -> $new"
  # Only attempt replacement if the old token exists somewhere
  if grep -Rql "$old" .; then
    grep -rl "$old" . | while read -r file; do
      sed -i.bak "s/$old/$new/g" "$file"
    done
  fi
done

echo ">> Cleaning up backup files..."
find . -name "*.bak" -delete

echo ">> Done."
