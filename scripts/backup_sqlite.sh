#!/usr/bin/env bash
set -euo pipefail
DB=domus.db
STAMP=$(date +%F_%H%M%S)
mkdir -p backups
cp "$DB" "backups/${STAMP}_$DB"
echo "Backup -> backups/${STAMP}_$DB"
