"""Stripe Checkout helpers."""
import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
PUBLIC_URL = os.getenv("PUBLIC_URL", "").rstrip("/")


def create_checkout_session(user_id: int, tg_username: str = "") -> str:
    """Create a Stripe Checkout session and return the URL."""
    if not stripe.api_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured.")
    if not PRICE_ID:
        raise RuntimeError("STRIPE_PRICE_ID is not configured.")
    if not PUBLIC_URL:
        raise RuntimeError("PUBLIC_URL is not configured.")

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": PRICE_ID, "quantity": 1}],
        success_url=f"{PUBLIC_URL}/pay/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{PUBLIC_URL}/pay/cancel",
        client_reference_id=str(user_id),
        metadata={
            "telegram_user_id": str(user_id),
            "telegram_username": tg_username or "",
        },
    )
    return session.url, session.id


def refund_session(payment_intent_id: str):
    """Issue a full refund for a payment intent."""
    if not stripe.api_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured.")
    return stripe.Refund.create(payment_intent=payment_intent_id)
