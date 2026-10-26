"""Flask integration service: pulls customer/order payloads from an upstream system, transforms them,
retries on failure with backoff, and logs failed transactions. Run: python integration/gateway.py"""
import logging, time
import requests
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO); log = logging.getLogger("gateway")
app = Flask(__name__)
UPSTREAM = "http://localhost:8000"; TOKEN = "demo-token"; FAILED = []


def transform(raw: dict) -> dict:
    """Map upstream customer/order payload to the platform's order schema."""
    if not raw.get("order_no") or not raw.get("cust_name"):
        raise ValueError("missing order_no or cust_name")
    return {"number": str(raw["order_no"]).strip().upper(), "customer": raw["cust_name"].strip().title()}


def with_retry(fn, tries=3, base=0.2):
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa
            log.warning("attempt %s failed: %s", i + 1, e)
            if i == tries - 1: raise
            time.sleep(base * 2 ** i)


@app.post("/sync")
def sync():
    try:
        payload = transform(request.get_json(force=True))
    except (ValueError, TypeError) as e:
        FAILED.append({"error": str(e)}); log.error("transform failed: %s", e); return jsonify(error=str(e)), 422
    try:
        r = with_retry(lambda: requests.post(f"{UPSTREAM}/api/requests/", json={"order": payload["number"], "title": "Sync " + payload["number"]},
                                             headers={"Authorization": f"Bearer {TOKEN}"}, timeout=3))
        return jsonify(upstream_status=r.status_code, payload=payload)
    except Exception as e:  # noqa
        FAILED.append({"payload": payload, "error": str(e)}); log.error("transaction failed: %s", e)
        return jsonify(error="upstream unavailable", queued=True), 502


@app.get("/failed")
def failed(): return jsonify(FAILED)

if __name__ == "__main__": app.run(port=5001)
