# Drop-in launcher that wraps your existing FastAPI app with:
# - OIDC JWT auth (when AUTH_ENABLED=true)
# - Prometheus request metrics
#
# Usage (Docker CMD):
#   uvicorn app_secured:app --host 0.0.0.0 --port 8000
#
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json, time, httpx, asyncio
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError

from settings import settings
from metrics_ext import MetricsMiddleware

# Import your existing app object (must be named 'app') from your current entrypoint
try:
    from main import app as base_app  # change if your file isn't main.py
except Exception as e:
    raise RuntimeError(f"Failed to import 'app' from main.py: {e}")

app = base_app

# -------- Metrics -------
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)

# -------- OIDC / JWT -------
OPEN_PATHS = {"/health", "/ready", "/metrics", "/docs", "/openapi.json"}

_jwks_cache = {'keys': None, 'iss': None, 'ts': 0}
_jwks_lock = asyncio.Lock()

async def _fetch_openid_config(authority: str):
    url = authority.rstrip('/') + '/.well-known/openid-configuration'
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.json()

async def _get_jwks():
    async with _jwks_lock:
        now = time.time()
        if _jwks_cache['keys'] and (now - _jwks_cache['ts'] < 3600):
            return _jwks_cache['keys'], _jwks_cache['iss']
        if not settings.OIDC_AUTHORITY and not settings.OIDC_JWKS_URI:
            raise RuntimeError("OIDC_AUTHORITY or OIDC_JWKS_URI must be set when AUTH_ENABLED=true")
        if settings.OIDC_JWKS_URI:
            jwks_uri = settings.OIDC_JWKS_URI
            issuer = settings.OIDC_ISSUER or settings.OIDC_AUTHORITY
        else:
            conf = await _fetch_openid_config(settings.OIDC_AUTHORITY)  # type: ignore
            jwks_uri = conf['jwks_uri']
            issuer = settings.OIDC_ISSUER or conf.get('issuer')
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(jwks_uri)
            r.raise_for_status()
            jwks = r.json()
        _jwks_cache.update({'keys': jwks, 'iss': issuer, 'ts': now})
        return jwks, issuer

class OIDCMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.AUTH_ENABLED:
            return await call_next(request)
        if request.url.path in OPEN_PATHS or request.method == 'OPTIONS':
            return await call_next(request)

        auth = request.headers.get('authorization') or request.headers.get('Authorization')
        if not auth or not auth.lower().startswith('bearer '):
            return JSONResponse({'detail': 'Unauthorized'}, status_code=401)

        token = auth.split(' ', 1)[1].strip()

        try:
            jwks, issuer = await _get_jwks()
            unverified = jwt.get_unverified_header(token)
            kid = unverified.get('kid')
            keys = jwks.get('keys', [])
            key = next((k for k in keys if k.get('kid') == kid), None)
            if not key:
                # fall back to first key if no kid match
                if keys:
                    key = keys[0]
                else:
                    return JSONResponse({'detail':'JWKS has no keys'}, status_code=401)

            algs = [a.strip() for a in (settings.OIDC_ALLOWED_ALGS or 'RS256').split(',')]
            claims = jwt.decode(
                token,
                key,
                algorithms=algs,
                audience=settings.OIDC_AUDIENCE,
                issuer=issuer
            )
            request.state.user = claims
        except ExpiredSignatureError:
            return JSONResponse({'detail': 'Token expired'}, status_code=401)
        except JWTClaimsError as ex:
            return JSONResponse({'detail': f'Invalid token claims: {ex}'}, status_code=401)
        except JWTError as ex:
            return JSONResponse({'detail': f'Invalid token: {ex}'}, status_code=401)
        except Exception as ex:
            return JSONResponse({'detail': f'Auth error: {ex}'}, status_code=401)

        return await call_next(request)

# Attach middleware
app.add_middleware(OIDCMiddleware)
