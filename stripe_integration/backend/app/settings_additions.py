"""
Additions to backend/app/settings.py — add these 4 fields to the Settings class.
"""

# Stripe
stripe_secret_key: str = ""
stripe_webhook_secret: str = ""
stripe_pro_price_id: str = ""           # e.g. price_1ABC...  (from Stripe dashboard)
frontend_url: str = "https://lcsengine.com"  # used for redirect URLs after checkout
