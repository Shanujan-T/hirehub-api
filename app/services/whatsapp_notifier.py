"""WhatsApp alerts via Twilio sandbox (optional — logs when not configured)."""

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


def _normalize_whatsapp_number(number: str) -> str:
    cleaned = (number or "").strip().replace(" ", "")
    if not cleaned:
        return ""
    if cleaned.startswith("whatsapp:"):
        return cleaned
    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"
    return f"whatsapp:{cleaned}"


def send_whatsapp_message(to_number: str, body: str) -> bool:
    """
    Send a WhatsApp message using Twilio's REST API.
    Returns True when sent (or simulated in demo mode), False on failure.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv(
        "TWILIO_WHATSAPP_FROM",
        "whatsapp:+14155238886",
    ).strip()

    to = _normalize_whatsapp_number(to_number)
    if not to:
        return False

    if not account_sid or not auth_token:
        logger.info(
            "[WhatsApp demo] To=%s Message=%s (set TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN to send for real)",
            to,
            body[:120],
        )
        return True

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = urllib.parse.urlencode(
        {"From": from_number, "To": to, "Body": body},
    ).encode()
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read().decode())
            logger.info("WhatsApp sent sid=%s", result.get("sid"))
            return True
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        logger.warning("WhatsApp send failed (%s): %s", exc.code, detail[:200])
        return False
    except Exception as exc:
        logger.warning("WhatsApp send failed: %s", exc)
        return False
