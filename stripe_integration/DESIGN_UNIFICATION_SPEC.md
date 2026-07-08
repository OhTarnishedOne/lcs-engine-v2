# LCS Engine — Design Unification Spec
## Claude Code Implementation Guide

The design system is already solid (tokens in globals.css are correct).
The gaps are inconsistency in HOW those tokens are applied across pages.
This spec fixes that + adds the paywall gates + CPI loop.

---

## 1. Design problems to fix

### 1A. Hardcoded colors vs CSS variables
Many components use raw hex (`#111827`, `#1A2942`, `#00D4AA`) instead of
the CSS variables already defined in globals.css. This makes theming fragile.

**Rule going forward:**
- `#0A1628` → `var(--lcs-primary)` or `bg-[#0A1628]` (Tailwind OK)
- `#111827` → `var(--lcs-surface)` or `bg-[#111827]`
- `#1A2942` → `var(--lcs-primary-light)` or `bg-[#1A2942]`
- `#00D4AA` → `var(--lcs-accent)` or `text-[#00D4AA]`
- `#9CA3AF` → `text-gray-400` ✓ (already consistent)

Don't do a global find-replace — just apply consistently in new/touched files.

### 1B. Card inconsistency
Some cards: `border border-gray-800 bg-[#111827] p-6`
Others: `border border-gray-700/50 bg-[#0D1B2A] p-4`
Others: `rounded-xl border border-gray-800 bg-[#111827] p-5`

**Standardize to one pattern for all content cards:**
```tsx
className="rounded-xl border border-gray-800 bg-[#111827] p-5"
```

**And one pattern for elevated/modal cards:**
```tsx
className="rounded-xl border border-gray-700 bg-[#1F2937] p-6"
```

### 1C. Header user menu — "Free Plan" is hardcoded
In `components/layout/header.tsx` line ~67:
```tsx
<p className="text-xs text-gray-500">Free Plan</p>
```
This needs to be dynamic once billing is live. Fix now with `useBillingStatus`:
```tsx
<p className="text-xs text-gray-500">{isPro ? "Pro" : "Free"} Plan</p>
```

### 1D. Sidebar version string
```tsx
<p className="text-xs text-gray-600">v2.0 • Phase 6</p>
```
Update to: `v3.0` — this is a public-facing string Joel will see.

### 1E. Sidebar — no Pro badge on locked items
Locked nav items (Probability Lab, Strategies for free users) should show
a subtle lock indicator so free users understand the tier boundary clearly.

### 1F. Homepage — missing demo CTA and pricing link
The homepage nav has Sign In + Get Started but no link to:
- The interactive demo (`demo.lcsengine.com` once live)
- Pricing page (`/pricing`)

These need to be added to the nav and below the hero CTA.

### 1G. Homepage — social proof is weak
"100+ Survey Respondents" is not a compelling trust signal for an
institutional buyer. Before 4/28, update to:
"6 active learners · 83% onboarding completion · Institutional pilots in progress"

---

## 2. New files to create

### 2A. `frontend/hooks/useBillingStatus.ts`
```typescript
"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export function useBillingStatus() {
  const { isAuthenticated } = useAuthStore();
  const { data, isLoading } = useQuery({
    queryKey: ["billing-status"],
    queryFn: () => api.getBillingStatus(),
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
  return {
    tier: data?.tier ?? "free",
    isPro: data?.is_pro ?? false,
    isLoading,
  };
}
```

### 2B. `frontend/hooks/useUpgrade.ts`
```typescript
"use client";
import { useState } from "react";
import { api } from "@/lib/api/client";

export function useUpgrade() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const upgrade = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { url } = await api.createCheckoutSession();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setIsLoading(false);
    }
  };
  return { upgrade, isLoading, error };
}
```

### 2C. `frontend/components/UpgradeBanner.tsx`
```tsx
"use client";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUpgrade } from "@/hooks/useUpgrade";

interface UpgradeBannerProps {
  feature?: string;
  className?: string;
}

export function UpgradeBanner({ feature = "this feature", className = "" }: UpgradeBannerProps) {
  const { upgrade, isLoading } = useUpgrade();
  return (
    <div className={`rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6 text-center ${className}`}>
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-[#00D4AA]/20">
        <Sparkles className="h-5 w-5 text-[#00D4AA]" />
      </div>
      <h3 className="text-base font-semibold text-white">Upgrade to Pro</h3>
      <p className="mt-1 text-sm text-gray-400">
        Unlock {feature} and everything else in Pro for $20/month.
      </p>
      <Button
        onClick={upgrade}
        disabled={isLoading}
        className="mt-4 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] disabled:opacity-60"
      >
        {isLoading ? "Redirecting…" : "Upgrade to Pro — $20/mo"}
      </Button>
    </div>
  );
}
```

### 2D. `frontend/components/UpgradeSuccessBanner.tsx`
```tsx
"use client";
import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle } from "lucide-react";

export function UpgradeSuccessBanner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (searchParams.get("upgrade") === "success") {
      setShow(true);
      queryClient.invalidateQueries({ queryKey: ["billing-status"] });
      const url = new URL(window.location.href);
      url.searchParams.delete("upgrade");
      router.replace(url.pathname + url.search, { scroll: false });
    }
  }, [searchParams, router, queryClient]);

  if (!show) return null;

  return (
    <div className="mb-6 flex items-center gap-3 rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
      <CheckCircle className="h-5 w-5 shrink-0 text-[#00D4AA]" />
      <div>
        <p className="text-sm font-semibold text-[#00D4AA]">You're now on Pro!</p>
        <p className="text-sm text-gray-400">All features are unlocked. Welcome to the full LCS Engine experience.</p>
      </div>
    </div>
  );
}
```

### 2E. `frontend/components/ProGate.tsx`
```tsx
"use client";
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";

interface ProGateProps {
  feature?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ProGate({ feature, children, fallback }: ProGateProps) {
  const { isPro, isLoading } = useBillingStatus();
  if (isLoading) return null;
  if (isPro) return <>{children}</>;
  return <>{fallback ?? <UpgradeBanner feature={feature} />}</>;
}
```

### 2F. `frontend/app/pricing/page.tsx`
Full pricing page at /pricing — Free vs Pro vs Institution.
(Full code in INTEGRATION_GUIDE.md from the stripe_integration_v2.zip)

---

## 3. Files to modify

### 3A. `frontend/lib/api/client.ts`
Add these two methods to the ApiClient class:

```typescript
async createCheckoutSession(): Promise<{ url: string }> {
  return this.post<{ url: string }>("/billing/create-checkout-session");
}

async getBillingStatus(): Promise<{ tier: string; is_pro: boolean }> {
  return this.get<{ tier: string; is_pro: boolean }>("/billing/status");
}
```

### 3B. `frontend/components/layout/header.tsx`
Three changes:

1. Add import at top:
```tsx
import { useBillingStatus } from "@/hooks/useBillingStatus";
```

2. Add inside Header() function:
```tsx
const { isPro } = useBillingStatus();
```

3. Replace hardcoded "Free Plan":
```tsx
// Before:
<p className="text-xs text-gray-500">Free Plan</p>
// After:
<p className="text-xs text-gray-500">{isPro ? "Pro" : "Free"} Plan</p>
```

4. Add Pro badge next to plan label when isPro:
```tsx
<div className="flex items-center gap-1.5">
  <p className="text-xs text-gray-500">{isPro ? "Pro" : "Free"} Plan</p>
  {isPro && (
    <span className="rounded-full bg-[#00D4AA]/20 px-1.5 py-0.5 text-[10px] font-semibold text-[#00D4AA]">
      PRO
    </span>
  )}
</div>
```

### 3C. `frontend/components/layout/sidebar.tsx`
Three changes:

1. Update version string:
```tsx
// Before:
<p className="text-xs text-gray-600">v2.0 • Phase 6</p>
// After:
<p className="text-xs text-gray-600">v3.0</p>
```

2. Add import:
```tsx
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { Lock } from "lucide-react";
```

3. Add lock indicator on gated nav items in NavLinks():
```tsx
// Add isPro to NavLinks:
const { isPro } = useBillingStatus();

// Define which routes are Pro-only:
const PRO_ROUTES = new Set(["/probability-lab", "/paper-trade"]);

// In the nav link render, add lock badge:
<Link key={item.name} href={item.href} ...>
  <item.icon className={...} />
  {item.name}
  {PRO_ROUTES.has(item.href) && !isPro && (
    <Lock className="ml-auto h-3 w-3 text-gray-600" />
  )}
</Link>
```

### 3D. `frontend/app/(dashboard)/dashboard/page.tsx`
Add at top of JSX return, before everything else:

```tsx
import { UpgradeSuccessBanner } from "@/components/UpgradeSuccessBanner";

// First line inside the outermost div:
<UpgradeSuccessBanner />
```

Also add upgrade CTA card at bottom of dashboard for free users:
```tsx
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { useUpgrade } from "@/hooks/useUpgrade";

// Inside DashboardPage():
const { isPro } = useBillingStatus();
const { upgrade, isLoading: upgradeLoading } = useUpgrade();

// After the quick actions grid, add:
{!isPro && (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: 0.4 }}
    className="mt-6 rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-6 flex items-center justify-between gap-4"
  >
    <div>
      <p className="font-semibold text-white">Unlock the full platform</p>
      <p className="text-sm text-gray-400 mt-0.5">
        Probability Lab, paper trading, unlimited AI tutor, and AI strategies — all for $20/month.
      </p>
    </div>
    <Button
      onClick={upgrade}
      disabled={upgradeLoading}
      className="shrink-0 bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
    >
      Upgrade to Pro
    </Button>
  </motion.div>
)}
```

### 3E. `frontend/app/(dashboard)/probability-lab/page.tsx`
Wrap main return in ProGate. The loading skeleton return stays untouched.

```tsx
import { ProGate } from "@/components/ProGate";

// The final return (after the marketsLoading check):
return (
  <ProGate feature="the Probability Lab">
    <div className="mx-auto max-w-6xl">
      {/* all existing JSX unchanged */}
    </div>
  </ProGate>
);
```

### 3F. `frontend/app/(dashboard)/paper-trade/page.tsx`
Same pattern as probability lab:
```tsx
import { ProGate } from "@/components/ProGate";

return (
  <ProGate feature="paper trading">
    <div className="mx-auto max-w-6xl">
      {/* all existing JSX unchanged */}
    </div>
  </ProGate>
);
```

### 3G. `frontend/app/(dashboard)/strategies/page.tsx`
Surgical gate — free users see the page but can't generate.

Add imports:
```tsx
import { useBillingStatus } from "@/hooks/useBillingStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";
```

Add inside StrategiesPage():
```tsx
const { isPro } = useBillingStatus();
```

Replace generate button (~line 182):
```tsx
{isPro ? (
  <Button
    onClick={() => generateMutation.mutate(undefined)}
    disabled={generateMutation.isPending}
    className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
  >
    {generateMutation.isPending ? (
      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
    ) : (
      <Plus className="mr-2 h-4 w-4" />
    )}
    Generate Strategy
  </Button>
) : (
  <Button
    onClick={() => window.location.href = "/pricing"}
    className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0]"
  >
    <Sparkles className="mr-2 h-4 w-4" />
    Upgrade to Generate
  </Button>
)}
```

Replace EmptyState (~line 255):
```tsx
{strategies.length === 0 ? (
  isPro ? (
    <EmptyState
      icon={Sparkles}
      title="No strategies yet"
      description="Generate your first AI-powered investment strategy to get started."
      action={{ label: "Generate Strategy", onClick: () => generateMutation.mutate(undefined) }}
    />
  ) : (
    <UpgradeBanner feature="AI-generated investment strategies" />
  )
) : (
  <div className="grid gap-6 md:grid-cols-2">
    {/* existing strategy cards unchanged */}
  </div>
)}
```

### 3H. `frontend/app/page.tsx` (homepage)
Four changes:

1. Add "Try Demo" button to nav (next to Sign In):
```tsx
<a href="https://demo.lcsengine.com" target="_blank" rel="noopener noreferrer">
  <Button variant="ghost" className="text-sm text-gray-300 hover:text-white hover:bg-white/5">
    Try Demo
  </Button>
</a>
```

2. Add pricing link to nav:
```tsx
<Link href="/pricing">
  <Button variant="ghost" className="text-sm text-gray-300 hover:text-white hover:bg-white/5">
    Pricing
  </Button>
</Link>
```

3. Add secondary CTA below the primary button:
```tsx
// After the "Get Started For Free" button:
<Link href="/pricing" className="text-sm text-gray-500 hover:text-gray-400 transition-colors">
  See pricing →
</Link>
```

4. Update social proof copy:
```tsx
// Before:
"100+ Survey Respondents · Paper trading only — no real money at risk"
// After:
"6 active learners · 83% onboarding completion · Institutional pilots in progress"
```

---

## 4. Backend — Stripe + billing router

### 4A. `backend/requirements.txt`
Add:
```
stripe>=7.0.0
```

### 4B. `backend/app/billing/__init__.py`
Create empty file.

### 4C. `backend/app/billing/schemas.py`
```python
from pydantic import BaseModel

class CreateCheckoutSessionRequest(BaseModel):
    pass

class CheckoutSessionResponse(BaseModel):
    url: str

class BillingStatusResponse(BaseModel):
    tier: str
    is_pro: bool
```

### 4D. `backend/app/billing/router.py`
Full file from stripe_integration_v2.zip → backend/app/billing/router.py

### 4E. `backend/app/db/models/user.py`
Add two fields to User model:
```python
tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
stripe_customer_id: Mapped[str | None] = mapped_column(
    String(100), unique=True, nullable=True, index=True
)
```

### 4F. `backend/app/settings.py`
Add to Settings class:
```python
stripe_secret_key: str = ""
stripe_webhook_secret: str = ""
stripe_pro_price_id: str = ""
frontend_url: str = "https://lcsengine.com"
```

### 4G. `backend/app/main.py`
Add 2 lines:
```python
from .billing.router import router as billing_router
# ...after other router includes:
app.include_router(billing_router, prefix="/api")
```

### 4H. Alembic migration
```bash
# Run after all model changes:
alembic revision --autogenerate -m "add stripe fields to users"
alembic upgrade head
```

---

## 5. CPI → Strategy loop

### 5A. `backend/app/probability/schemas.py`
Add:
```python
class MacroStrategyRequest(BaseModel):
    market_id: str
    market_title: str
    user_prediction: float
```

### 5B. `backend/app/probability/router.py`
Add endpoint (full code in SESSION_LIMIT_AND_CPI_LOOP_SPEC.md):
```python
@router.post("/macro-strategy")
async def get_macro_strategy(request, current_user, db, ai_client):
    # Pro only gate
    # Fetch user profile for archetype
    # Build prompt with direction + archetype + risk tolerance
    # Return JSON strategy
```

### 5C. `frontend/components/MacroStrategyCard.tsx`
Full component from SESSION_LIMIT_AND_CPI_LOOP_SPEC.md.
Shows thesis, allocation bars, risk note, learning point.
Only appears after prediction is submitted and user is Pro.

### 5D. `frontend/app/(dashboard)/probability-lab/page.tsx`
After the showResult block inside the modal, add:
```tsx
import { MacroStrategyCard } from "@/components/MacroStrategyCard";

{showResult && selectedMarket && isPro && (
  <MacroStrategyCard
    marketId={selectedMarket.id}
    marketTitle={selectedMarket.title}
    userPrediction={probability}
  />
)}
{showResult && selectedMarket && !isPro && (
  <div className="mt-4">
    <UpgradeBanner feature="macro-to-portfolio strategy insights" />
  </div>
)}
```

---

## 6. Session limit (chat)

### 6A. `backend/app/chat/router.py`
Add session status endpoint + guard on POST /messages.
Full code in SESSION_LIMIT_AND_CPI_LOOP_SPEC.md.

### 6B. `frontend/lib/api/client.ts`
Add:
```typescript
async getSessionStatus(): Promise<{
  conversation_count: number;
  limit: number;
  limit_reached: boolean;
  is_pro: boolean;
}> {
  return this.get("/chat/session-status");
}
```

### 6C. `frontend/hooks/useSessionStatus.ts`
Full hook from SESSION_LIMIT_AND_CPI_LOOP_SPEC.md.

### 6D. `frontend/app/(dashboard)/chat/page.tsx`
Gate new conversation button and input on `limitReached`.
Full changes in SESSION_LIMIT_AND_CPI_LOOP_SPEC.md.

---

## 7. Claude Code prompt to paste

Copy and paste this verbatim into Claude Code after opening the repo:

---

I need you to implement a full set of changes across the LCS Engine codebase.
Context: this is a Next.js 16 + FastAPI fintech app. Read CLAUDE.md first.

Work through these in order. Complete each group fully before moving to the next.

**Group 1 — New hooks and components (create these files):**
- frontend/hooks/useBillingStatus.ts
- frontend/hooks/useUpgrade.ts
- frontend/hooks/useSessionStatus.ts
- frontend/components/ProGate.tsx
- frontend/components/UpgradeBanner.tsx
- frontend/components/UpgradeSuccessBanner.tsx
- frontend/components/MacroStrategyCard.tsx
- frontend/app/pricing/page.tsx

All code is in DESIGN_UNIFICATION_SPEC.md and SESSION_LIMIT_AND_CPI_LOOP_SPEC.md.

**Group 2 — Frontend modifications:**
- frontend/lib/api/client.ts: add createCheckoutSession() and getBillingStatus() and getSessionStatus() methods
- frontend/components/layout/header.tsx: dynamic tier badge, useBillingStatus
- frontend/components/layout/sidebar.tsx: v3.0, lock icons on Pro routes
- frontend/app/(dashboard)/dashboard/page.tsx: UpgradeSuccessBanner + Pro upgrade CTA
- frontend/app/(dashboard)/probability-lab/page.tsx: ProGate wrap + MacroStrategyCard after prediction
- frontend/app/(dashboard)/paper-trade/page.tsx: ProGate wrap
- frontend/app/(dashboard)/strategies/page.tsx: isPro gate on generate button + EmptyState
- frontend/app/(dashboard)/chat/page.tsx: session limit gate on new conversation + input
- frontend/app/page.tsx: Try Demo button, Pricing link in nav, updated social proof copy

**Group 3 — Backend (Stripe + CPI loop):**
- Add stripe>=7.0.0 to backend/requirements.txt
- Create backend/app/billing/__init__.py, schemas.py, router.py
- Modify backend/app/db/models/user.py: add tier + stripe_customer_id fields
- Modify backend/app/settings.py: add stripe_secret_key, stripe_webhook_secret, stripe_pro_price_id, frontend_url
- Modify backend/app/main.py: import and register billing_router
- Modify backend/app/probability/schemas.py: add MacroStrategyRequest
- Modify backend/app/probability/router.py: add /macro-strategy endpoint
- Modify backend/app/chat/router.py: add /session-status endpoint + guard on POST /messages

**Group 4 — Database migration:**
After all model changes:
```bash
cd backend && alembic revision --autogenerate -m "add stripe fields to users" && alembic upgrade head
```

Run `npm run build` in frontend/ and `pytest` in backend/ after completion to verify nothing broke.

---
