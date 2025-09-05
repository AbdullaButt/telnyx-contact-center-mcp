from __future__ import annotations
import os, uuid, logging
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from analytics_db import save_call_if_new, log_event, log_ivr_selection, log_transfer

# --- Env / Config -----------------------------------------------------------
load_dotenv(Path(__file__).with_name(".env"), override=True)
TELNYX_API_KEY = (os.getenv("TELNYX_API_KEY") or "").strip()
if not TELNYX_API_KEY or not TELNYX_API_KEY.startswith("KEY"):
    raise RuntimeError("Set TELNYX_API_KEY=KEY... in .env")

API_BASE = "https://api.telnyx.com/v2"
HTTP_TIMEOUT = 8

def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

# --- App / Logging -----------------------------------------------------------
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ivr")

# --- Departments (1/2/3) ----------------------------------------------------
DEPARTMENT_URIS: Dict[str, str] = {
    "sales":   os.getenv("SALES_SIP_URI", "sip:agent1@sip.telnyx.com"),
    "support": os.getenv("SUPPORT_SIP_URI", "sip:agent2@sip.telnyx.com"),
    "porting": os.getenv("PORTING_SIP_URI", "sip:agent3@sip.telnyx.com"),
}
DIGIT_TO_DEPARTMENT: Dict[str, str] = {"1": "sales", "2": "support", "3": "porting"}

# Track to avoid duplicate/late commands
ROUTED_CALLS: set[str] = set()
ENDED_CALLS: set[str] = set()

# --- Telnyx Call Control helpers -------------------------------------------
def _post(url: str, body: Dict[str, Any]) -> Optional[requests.Response]:
    try:
        return requests.post(url, json=body, headers=_headers(), timeout=HTTP_TIMEOUT)
    except Exception as e:
        log.error("POST %s failed: %s", url, e)
        return None

def answer_call(ccid: str) -> bool:
    r = _post(f"{API_BASE}/calls/{ccid}/actions/answer", {"command_id": str(uuid.uuid4())})
    ok = bool(r and r.status_code == 200)
    if not ok:
        log.error("answer failed: %s %s", getattr(r, "status_code", None), getattr(r, "text", ""))
    return ok

def transfer_call(ccid: str, sip_uri: str) -> bool:
    body = {"to": sip_uri, "command_id": str(uuid.uuid4())}
    r = _post(f"{API_BASE}/calls/{ccid}/actions/transfer", body)
    ok = bool(r and r.status_code == 200)
    if not ok:
        log.error("transfer failed: %s %s", getattr(r, "status_code", None), getattr(r, "text", ""))
    return ok

def start_menu(ccid: str) -> None:
    """DTMF menu only."""
    body = {
        "payload": (
            "Welcome to Telnyx Contact Center. "
            "For Sales, press 1. For Support, press 2. For Porting, press 3."
        ),
        "invalid_payload": "Sorry, try again. 1 for Sales, 2 for Support, 3 for Porting.",
        "payload_type": "text",
        "service_level": "premium",
        "voice": "Telnyx.KokoroTTS.af",
        "minimum_digits": 1,
        "maximum_digits": 1,
        "valid_digits": "123",
        "timeout_millis": 8000,
        "command_id": str(uuid.uuid4()),
    }
    r = _post(f"{API_BASE}/calls/{ccid}/actions/gather_using_speak", body)
    if not (r and r.status_code == 200):
        log.error("start_menu failed: %s %s", getattr(r, "status_code", None), getattr(r, "text", ""))

def _extract_digits(event_payload: Dict[str, Any]) -> str:
    d = event_payload.get("digit") or event_payload.get("digits")
    if d:
        return str(d).strip()
    res = event_payload.get("result") or event_payload.get("dtmf") or {}
    if isinstance(res, dict):
        return str(res.get("digits") or res.get("digit") or "").strip()
    return ""

# --- Webhook ----------------------------------------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    data = payload.get("data", {})
    etype = data.get("event_type")
    ev = data.get("payload", {})

    try:
        if etype == "call.initiated":
            ccid = ev.get("call_control_id")
            from_number = ev.get("from") or "unknown"
            to_number = ev.get("to") or "unknown"
            
            if not ccid:
                return jsonify({"status": "missing_call_control_id"}), 200
            
            # Save call to analytics database
            save_call_if_new(ccid, from_number, to_number)
            log_event(ccid, "call.initiated", ev)
            
            if not answer_call(ccid):
                return jsonify({"status": "answer_failed"}), 200
            start_menu(ccid)
            return jsonify({"status": "answered_and_menu_started"}), 200

        # DTMF flow: rely on gather end; ignore per-digit events
        elif etype == "call.gather.ended":
            ccid = ev.get("call_control_id")
            if not ccid or ccid in ROUTED_CALLS or ccid in ENDED_CALLS:
                return jsonify({"status": "gather_ignored"}), 200
            
            # Log gather event
            log_event(ccid, "call.gather.ended", ev)
            
            digit = _extract_digits(ev)
            dept = DIGIT_TO_DEPARTMENT.get(digit or "")
            
            if dept:
                # Log IVR selection
                log_ivr_selection(ccid, digit, dept)
                
                to_uri = DEPARTMENT_URIS[dept]
                transfer_success = transfer_call(ccid, to_uri)
                
                # Log transfer attempt
                log_transfer(ccid, to_uri, "success" if transfer_success else "error")
                
                if transfer_success:
                    ROUTED_CALLS.add(ccid)
            else:
                start_menu(ccid)  # replay
            return jsonify({"status": "gather_processed", "digit": digit}), 200

        elif etype == "call.hangup":
            ccid = ev.get("call_control_id")
            if ccid:
                # Log hangup event
                log_event(ccid, "call.hangup", ev)
                ENDED_CALLS.add(ccid)
            return jsonify({"status": "received"}), 200

        # Log all other events for debugging
        elif etype:
            ccid = ev.get("call_control_id")
            if ccid:
                log_event(ccid, etype, ev)

        # Everything else can be acknowledged silently
        return jsonify({"status": "received", "event": etype}), 200

    except Exception as e:
        logging.exception("webhook error: %s", e)
        # Still return 200 to prevent Telnyx retries
        return jsonify({"status": "error"}), 200

# --- Run --------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    log.info("Starting on :%s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
