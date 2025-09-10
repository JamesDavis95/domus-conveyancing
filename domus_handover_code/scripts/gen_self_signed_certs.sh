#!/usr/bin/env bash
set -euo pipefail
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes -keyout certs/privkey.pem -out certs/fullchain.pem -days 365 -subj "/CN=example.com"
echo "Self-signed certs written to ./certs (for local Caddy tls internal/testing)."
