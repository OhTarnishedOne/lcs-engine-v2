from pydantic import BaseModel


class CreateCheckoutSessionRequest(BaseModel):
    """Request body for creating a Stripe Checkout session. Currently empty —
    price_id comes from server config so the client can't inject a different tier."""
    pass


class CheckoutSessionResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    tier: str       # "free" | "pro" | "institution"
    is_pro: bool
