import logging
import stripe

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..db.models.user import User
from ..settings import get_settings
from .schemas import CreateCheckoutSessionRequest, CheckoutSessionResponse, BillingStatusResponse

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/billing", tags=["billing"])


def get_stripe():
    stripe.api_key = settings.stripe_secret_key
    return stripe


# ---------------------------------------------------------------------------
# POST /api/billing/create-checkout-session
# Creates a Stripe Checkout session for Free → Pro upgrade.
# ---------------------------------------------------------------------------
@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    data: CreateCheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionResponse:
    get_stripe()

    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Billing not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.stripe_pro_price_id,
                    "quantity": 1,
                }
            ],
            customer_email=current_user.email,
            client_reference_id=current_user.id,
            success_url=f"{settings.frontend_url}/dashboard?upgrade=success",
            cancel_url=f"{settings.frontend_url}/dashboard?upgrade=cancelled",
            metadata={
                "user_id": current_user.id,
                "user_email": current_user.email,
            },
        )
        return CheckoutSessionResponse(url=session.url)

    except stripe.StripeError as e:
        logger.error(f"Stripe error for user {current_user.id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to create checkout session")


# ---------------------------------------------------------------------------
# GET /api/billing/status
# Returns the current user's tier (free or pro).
# ---------------------------------------------------------------------------
@router.get("/status", response_model=BillingStatusResponse)
def get_billing_status(
    current_user: User = Depends(get_current_user),
) -> BillingStatusResponse:
    return BillingStatusResponse(
        tier=current_user.tier,
        is_pro=current_user.tier == "pro",
    )


# ---------------------------------------------------------------------------
# POST /api/billing/webhook
# Handles Stripe webhook events. No auth — verified by signature.
# ---------------------------------------------------------------------------
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    get_stripe()

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook parse error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    logger.info(f"Stripe webhook received: {event_type}")

    # ── Subscription activated (checkout completed) ──────────────────────
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id")
        _upgrade_user(db, user_id, stripe_customer_id=session.get("customer"))

    # ── Subscription renewed ─────────────────────────────────────────────
    elif event_type == "invoice.paid":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")
        _upgrade_user_by_customer(db, customer_id)

    # ── Subscription cancelled / payment failed ──────────────────────────
    elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
        obj = event["data"]["object"]
        customer_id = obj.get("customer")
        _downgrade_user_by_customer(db, customer_id)

    return {"received": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upgrade_user(db: Session, user_id: str, stripe_customer_id: str | None = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"Webhook: user {user_id} not found")
        return
    user.tier = "pro"
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    db.commit()
    logger.info(f"User {user_id} upgraded to pro")


def _upgrade_user_by_customer(db: Session, customer_id: str):
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"Webhook: no user found for customer {customer_id}")
        return
    user.tier = "pro"
    db.commit()
    logger.info(f"User {user.id} subscription renewed (pro)")


def _downgrade_user_by_customer(db: Session, customer_id: str):
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.warning(f"Webhook: no user found for customer {customer_id}")
        return
    user.tier = "free"
    db.commit()
    logger.info(f"User {user.id} downgraded to free")
