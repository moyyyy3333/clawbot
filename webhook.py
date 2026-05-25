"""Stripe webhook + success/cancel pages.

Run alongside bot.py:
    gunicorn -w 2 -b 0.0.0.0:$PORT webhook:app

Stripe must POST to ${PUBLIC_URL}/stripe/webhook
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv()

import stripe
from flask import Flask, request, jsonify, redirect

import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhook")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

app = Flask(__name__)
db.init_db()


@app.route("/", methods=["GET"])
def health():
    return "ClawBot webhook OK", 200


@app.route("/pay/success", methods=["GET"])
def pay_success():
    session_id = request.args.get("session_id", "")
    return (
        f"<h1>✅ Payment received!</h1>"
        f"<p>Head back to Telegram and send <code>/paid</code> to start your setup.</p>"
        f"<p style='color:#888'>session: {session_id}</p>",
        200,
    )


@app.route("/pay/cancel", methods=["GET"])
def pay_cancel():
    return "<h1>Payment cancelled.</h1><p>Head back to Telegram and try /buy again.</p>", 200


def _notify_user_paid(user_id: int):
    """Send Telegram notification that payment succeeded (best-effort)."""
    if not BOT_TOKEN:
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": user_id,
                "text": (
                    "✅ *Payment confirmed!* Welcome to ClawBot Premium 🦞\n\n"
                    "Send /paid here to kick off your 30-minute setup."
                ),
                "parse_mode": "Markdown",
            },
            timeout=8,
        )
    except Exception:
        log.exception("telegram notify failed")


@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception as e:
        log.warning("invalid webhook: %s", e)
        return jsonify({"error": "invalid signature"}), 400

    # Idempotency
    if db.stripe_event_seen(event["id"]):
        return jsonify({"received": True, "dedup": True}), 200

    etype = event["type"]
    obj = event["data"]["object"]
    log.info("stripe event: %s", etype)

    if etype == "checkout.session.completed":
        user_id = int(obj.get("client_reference_id") or 0)
        payment_intent = obj.get("payment_intent") or ""
        if user_id and payment_intent:
            db.mark_paid(user_id, payment_intent)
            db.log_event(user_id, "stripe_paid", {"pi": payment_intent})
            _notify_user_paid(user_id)

    elif etype in ("charge.refunded", "refund.created"):
        # Look up by payment_intent
        pi = obj.get("payment_intent") or obj.get("id")
        if pi:
            import sqlite3
            with sqlite3.connect(db.DB_PATH) as c:
                row = c.execute(
                    "SELECT user_id FROM users WHERE stripe_payment_intent = ?",
                    (pi,),
                ).fetchone()
                if row:
                    db.mark_refunded(row[0])
                    db.log_event(row[0], "stripe_refunded", {"pi": pi})

    return jsonify({"received": True}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
