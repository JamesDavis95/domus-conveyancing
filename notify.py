import json, logging, urllib.request

def send_email_console(to_email: str, subject: str, body: str) -> bool:
    logging.info("[EMAIL] to=%s | subject=%s\n%s", to_email, subject, body)
    return True

def send_webhook(url: str, payload: dict) -> bool:
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=5) as _:
            return True
    except Exception as e:
        logging.warning("Webhook failed: %s", e)
        return False
