# Stripe Integration — LCS Engine
## Free → Pro Checkout (Phase 0)

---

## Files in this package

| File | Action |
|------|--------|
| `backend/app/billing/router.py` | New file — copy to your repo |
| `backend/app/billing/schemas.py` | New file — copy to your repo |
| `backend/app/billing/__init__.py` | New file — copy to your repo |
| `backend/app/db/models/user.py` | Replace your existing file |
| `backend/app/settings_additions.py` | Add these 4 fields to your Settings class |
| `backend/app/main_diff.txt` | 2-line change to main.py |
| `backend/alembic/versions/add_stripe_fields.py` | New migration |
| `frontend/hooks/useUpgrade.ts` | New file |
| `frontend/hooks/useBillingStatus.ts` | New file |
| `frontend/components/UpgradeBanner.tsx` | New file |
| `frontend/components/UpgradeSuccessBanner.tsx` | New file |
| `frontend/components/ProGate.tsx` | New file |
| `frontend/app/pricing/page.tsx` | New file — creates /pricing route |
| `frontend/lib/api/billing_additions.ts` | Add these 2 methods to ApiClient |

---

## Setup steps

### 1. Stripe Dashboard
1. Create a **Product** called "LCS Engine Pro"
2. Add a **Price**: $20/month recurring → copy the `price_...` ID
3. Create a **Webhook** endpoint pointing to:
   `https://lcs-engine-v2-production.up.railway.app/api/billing/webhook`
4. Subscribe to these events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
5. Copy the webhook signing secret (`whsec_...`)

### 2. Backend

```bash
# Add stripe to requirements.txt
echo "stripe>=7.0.0" >> backend/requirements.txt

# Copy billing module
cp -r backend/app/billing/ your-repo/backend/app/billing/

# Replace User model (adds tier + stripe_customer_id)
cp backend/app/db/models/user.py your-repo/backend/app/db/models/user.py

# Add 4 fields to Settings class in settings.py:
# stripe_secret_key, stripe_webhook_secret, stripe_pro_price_id, frontend_url

# Add 2 lines to main.py:
# from .billing.router import router as billing_router
# app.include_router(billing_router, prefix="/api")

# Run migration (get your current head first)
cd your-repo/backend
alembic heads   # copy the revision ID
# Edit add_stripe_fields.py → set down_revision to that ID
alembic revision --autogenerate -m "add stripe fields"  # or use the provided file
alembic upgrade head
```

### 3. Railway env vars
Add in Railway → your backend service → Variables:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRO_PRICE_ID=price_...
FRONTEND_URL=https://lcsengine.com
```

### 4. Frontend

```bash
# Copy hooks
cp frontend/hooks/useUpgrade.ts your-repo/frontend/hooks/
cp frontend/hooks/useBillingStatus.ts your-repo/frontend/hooks/

# Copy components
cp frontend/components/UpgradeBanner.tsx your-repo/frontend/components/
cp frontend/components/UpgradeSuccessBanner.tsx your-repo/frontend/components/
cp frontend/components/ProGate.tsx your-repo/frontend/components/

# Add pricing page
mkdir -p your-repo/frontend/app/pricing
cp frontend/app/pricing/page.tsx your-repo/frontend/app/pricing/

# Add 2 methods to lib/api/client.ts
# (see frontend/lib/api/billing_additions.ts)
```

### 5. Wire up the upgrade flow

**Dashboard page** — add the success banner:
```tsx
import { UpgradeSuccessBanner } from "@/components/UpgradeSuccessBanner";
// Inside your dashboard component:
<UpgradeSuccessBanner />
```

**Gate a Pro feature** (e.g. unlimited chat):
```tsx
import { ProGate } from "@/components/ProGate";
<ProGate feature="unlimited AI tutor sessions">
  <ChatInterface />
</ProGate>
```

**Standalone upgrade button anywhere**:
```tsx
import { useUpgrade } from "@/hooks/useUpgrade";
const { upgrade, isLoading } = useUpgrade();
<Button onClick={upgrade} disabled={isLoading}>
  {isLoading ? "Redirecting…" : "Upgrade to Pro"}
</Button>
```

---

## Test checklist (use Stripe test mode first)

- [ ] `sk_test_...` in Railway (test mode)
- [ ] Click upgrade → redirects to Stripe Checkout
- [ ] Use test card `4242 4242 4242 4242` → completes
- [ ] Returns to `/dashboard?upgrade=success` → banner shows
- [ ] `GET /api/billing/status` returns `{ tier: "pro", is_pro: true }`
- [ ] Pro-gated features unlock without page refresh
- [ ] Webhook fires → Railway logs show "User upgraded to pro"
- [ ] Swap to `sk_live_...` for production

---

## Flow diagram

```
User clicks "Upgrade"
       ↓
POST /api/billing/create-checkout-session
       ↓
Stripe Checkout (hosted by Stripe)
       ↓ (on success)
Stripe fires webhook → POST /api/billing/webhook
       ↓
User.tier = "pro" in DB
       ↓ (simultaneously)
Browser redirects → /dashboard?upgrade=success
       ↓
UpgradeSuccessBanner shows, billing-status cache invalidated
       ↓
useBillingStatus refetches → isPro = true → features unlock
```
