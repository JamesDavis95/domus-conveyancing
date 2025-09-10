from settings import settings
import clamd

def scan_bytes(data: bytes) -> None:
    if not settings.AV_SCAN:
        return
    cd = clamd.NetworkSocket(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
    res = cd.instream(data)
    status = res.get("stream", ["OK","OK"])[0]
    if status != "OK":
        raise ValueError(f"AV blocked: {res}")
