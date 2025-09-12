import os, time, hmac, hashlib, base64

def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64u_dec(s: str) -> bytes:
    pad = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)

def make_token(matter_id: int, ttl_seconds: int = None) -> str:
    secret = (os.getenv("SECRET_KEY") or "dev-secret").encode("utf-8")
    ttl = int(ttl_seconds or int(os.getenv("PUBLISH_TTL_SECONDS", "2592000")))  # 30d default
    exp = int(time.time()) + ttl
    payload = f"{matter_id}.{exp}".encode("utf-8")
    sig = hmac.new(secret, payload, hashlib.sha256).digest()
    return _b64u(payload) + "." + _b64u(sig)

def verify_token(token: str, matter_id: int) -> bool:
    try:
        p_b64, s_b64 = token.split(".", 1)
        payload = _b64u_dec(p_b64)
        sig = _b64u_dec(s_b64)
        secret = (os.getenv("SECRET_KEY") or "dev-secret").encode("utf-8")
        expect = hmac.new(secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expect): return False
        payload_str = payload.decode("utf-8")
        mid_str, exp_str = payload_str.split(".", 1)
        if int(mid_str) != int(matter_id): return False
        if time.time() > int(exp_str): return False
        return True
    except Exception:
        return False
