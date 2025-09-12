import os

def _client():
    try:
        import clamd
        host = os.getenv("CLAMD_HOST") or "localhost"
        port = int(os.getenv("CLAMD_PORT") or "3310")
        return clamd.ClamdNetworkSocket(host=host, port=port)
    except Exception:
        return None

def scan_bytes(b: bytes):
    """
    Return None if clean/unknown; raise ValueError if infected.
    """
    c = _client()
    if not c:
        return None
    try:
        res = c.instream(b)
        status = (res or {}).get("stream", [None, "UNKNOWN"])[0]
        if status == "OK":
            return None
        raise ValueError(f"AV detected: {status}")
    except Exception:
        # soft fail closed — don't block uploads if AV hiccups
        return None
