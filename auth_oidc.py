from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from settings import settings

router = APIRouter()
oauth = OAuth()
if settings.AUTH_ENABLED:
    oauth.register(
        name="azure",
        client_id=settings.OIDC_CLIENT_ID,
        client_secret=settings.OIDC_CLIENT_SECRET,
        server_metadata_url=f"{settings.OIDC_AUTHORITY}/.well-known/openid-configuration",
        client_kwargs={"scope": settings.OIDC_SCOPE},
    )

@router.get("/login")
async def login(request: Request):
    if not settings.AUTH_ENABLED:
        return RedirectResponse("/")
    redirect_uri = request.url_for("auth_callback")
    return await oauth.azure.authorize_redirect(request, redirect_uri)

@router.get(settings.OIDC_REDIRECT_PATH, name="auth_callback")
async def auth_callback(request: Request):
    if not settings.AUTH_ENABLED:
        return RedirectResponse("/")
    token = await oauth.azure.authorize_access_token(request)
    user = token.get("userinfo") or {}
    request.session["user"] = {"email": user.get("email") or user.get("preferred_username"), "sub": user.get("sub")}
    return RedirectResponse("/la/ui")

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
