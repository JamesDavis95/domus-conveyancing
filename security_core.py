import time
import json
from typing import Optional, Dict, Any
import httpx
from jose import jwt
import os
from fastapi import Request, HTTPException
from settings import settings

# Simple in-memory cache for JWKS
_JWKS_CACHE: Dict[str, Dict[str, Any]] = {}
_CFG_CACHE: Dict[str, Dict[str, Any]] = {}

SAFE_PATHS = {"/health", "/ready", "/docs", "/openapi.json"}

def _iss() -> Optional[str]:
    return (settings.OIDC_AUTHORITY or "").rstrip("/")

def _aud() -> Optional[str]:
    return settings.OIDC_CLIENT_ID or None

async def _get_openid_config(iss: str) -> Dict[str, Any]:
    cached = _CFG_CACHE.get(iss)
    if cached and cached.get("_exp", 0) > time.time():
        return cached
    url = f"{iss}/.well-known/openid-configuration"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        cfg = r.json()
    cfg["_exp"] = time.time() + 3600
    _CFG_CACHE[iss] = cfg
    return cfg

async def _get_jwk_for_kid(iss: str, kid: str) -> Optional[Dict[str, Any]]:
    jwks = _JWKS_CACHE.get(iss)
    if not jwks or jwks.get("_exp", 0) <= time.time():
        cfg = await _get_openid_config(iss)
        jwks_uri = cfg.get("jwks_uri")
        if not jwks_uri:
            return None
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(jwks_uri)
            r.raise_for_status()
            keys = r.json().get("keys", [])
        jwks = {"keys": keys, "_exp": time.time() + 3600}
        _JWKS_CACHE[iss] = jwks
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None

async def _verify_bearer(token: str) -> Dict[str, Any]:
    iss = _iss()
    aud = _aud()
    if not iss:
        raise HTTPException(401, "OIDC issuer not configured")
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    jwk = await _get_jwk_for_kid(iss, kid) if kid else None
    if not jwk:
        raise HTTPException(401, "Signing key not found")
    try:
        claims = jwt.decode(
            token,
            jwk,
            audience=aud,
            issuer=iss,
            options={"verify_aud": bool(aud)},
        )
        return claims
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

async def resolve_user(request: Request) -> Dict[str, Any]:
    """
    Returns a user dict:
      { "id": "...", "email": "...", "name": "...", "role": "admin|officer|viewer", "auth": "oidc|apikey|dev" }
    """
    if not settings.AUTH_ENABLED:
        return {"id": "dev", "email": "dev@example.org", "name": "Dev", "role": "admin", "auth": "dev"}

    authz = request.headers.get("authorization") or ""
    api_key = request.headers.get("x-api-key")

    if authz.lower().startswith("bearer "):
        token = authz.split(" ", 1)[1].strip()
        claims = await _verify_bearer(token)
        email = claims.get("email") or claims.get("upn") or claims.get("preferred_username")
        name = claims.get("name") or email or "User"
        # Minimal role mapping; customize via claim or directory group later
        role = "admin" if email and email.endswith("@example.gov.uk") else "officer"
        return {"id": claims.get("sub") or email or "user", "email": email, "name": name, "role": role, "auth": "oidc"}

    if api_key:
        # In dev, accept any API key. In prod, validate against DB or KMS.
        role = "admin" if api_key in {"demo-key", settings.SECRET_KEY} else "officer"
        return {"id": f"apikey:{api_key[:6]}", "email": None, "name": "API Key", "role": role, "auth": "apikey"}

    raise HTTPException(401, "Missing Authorization or X-Api-Key")

def roles_allowed(*roles: str):
    async def _check(request: Request):
        user = getattr(request.state, "user", None)
        if not user or user.get("role") not in roles:
            raise HTTPException(403, "Forbidden")
    return _check

def attach_security(app):
    @app.middleware("http")
    async SECURITY_ALLOWLIST = set(os.environ.get("SECURITY_ALLOWLIST", "/health,/ready,/openapi.json,/docs,/redoc,/metrics,/api/orgs,/").split(","))

def _auth_guard(request: Request, call_next):
        path = request.url.path
        if path in SAFE_PATHS:
            return await call_next(request)
        if path.startswith(("/api", "/la", "/jobs", "/metrics", "/admin")):
            user = await resolve_user(request)
            request.state.user = user
        return await call_next(request)
