# Chat session limit + CPI → Strategy loop
## Implementation spec

---

## Part 1 — Chat session limit (Free: 3 conversations)

### Decision: count conversations, not messages

The `Conversation` model already exists with `user_id` and `is_active`.
A "session" = one conversation. Free users get 3. Simple, already in the DB.

---

### Backend

**Add to `backend/app/chat/router.py`:**

```python
from ..db.models.chat import Conversation

FREE_CONVERSATION_LIMIT = 3

@router.get("/session-status")
def get_session_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns conversation count and whether the free limit is hit.
    Used by the frontend to gate new conversations for Free users.
    """
    count = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .count()
    )
    is_pro = current_user.tier == "pro"
    limit_reached = not is_pro and count >= FREE_CONVERSATION_LIMIT

    return {
        "conversation_count": count,
        "limit": FREE_CONVERSATION_LIMIT,
        "limit_reached": limit_reached,
        "is_pro": is_pro,
    }
```

**Also gate the `POST /chat/messages` endpoint itself** — defense in depth,
so a clever user can't just skip the frontend gate:

```python
@router.post("/messages")
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
):
    # Enforce free tier limit on new conversations only
    if not request.conversation_id and current_user.tier != "pro":
        count = (
            db.query(Conversation)
            .filter(Conversation.user_id == current_user.id)
            .count()
        )
        if count >= FREE_CONVERSATION_LIMIT:
            raise HTTPException(
                status_code=402,
                detail="Free plan limit reached. Upgrade to Pro for unlimited conversations."
            )

    async def event_stream():
        # ... existing code unchanged ...
```

No migration needed — querying existing `conversations` table.

---

### Frontend

**Add to `lib/api/client.ts`:**

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

**Add hook `hooks/useSessionStatus.ts`:**

```typescript
"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

export function useSessionStatus() {
  const { isAuthenticated } = useAuthStore();

  const { data, isLoading } = useQuery({
    queryKey: ["session-status"],
    queryFn: () => api.getSessionStatus(),
    enabled: isAuthenticated,
    // Refetch when conversations change
    staleTime: 0,
  });

  return {
    conversationCount: data?.conversation_count ?? 0,
    limitReached: data?.limit_reached ?? false,
    isPro: data?.is_pro ?? false,
    isLoading,
  };
}
```

**In `app/(dashboard)/chat/page.tsx`**, two changes:

1. Import and call the hook:
```typescript
import { useSessionStatus } from "@/hooks/useSessionStatus";
import { UpgradeBanner } from "@/components/UpgradeBanner";

// Inside ChatPage():
const { limitReached } = useSessionStatus();
```

2. Gate the "New Chat" button and the input area. Find where `+` / new
   conversation is triggered and wrap it:

```tsx
{/* New conversation button — already in your sidebar */}
{limitReached ? (
  <div className="p-3">
    <UpgradeBanner feature="unlimited AI tutor sessions" />
  </div>
) : (
  <Button onClick={handleNewConversation}>
    <Plus className="h-4 w-4 mr-2" /> New Chat
  </Button>
)}

{/* Bottom input area */}
{limitReached && !selectedConversationId ? (
  <div className="p-4">
    <UpgradeBanner feature="unlimited AI tutor sessions" />
  </div>
) : (
  // existing input JSX
)}
```

**Invalidate session-status after a new conversation is created:**

```typescript
// After a new conversation starts (in your SSE stream handler,
// when you receive the "start" event with a new conversation_id):
queryClient.invalidateQueries({ queryKey: ["session-status"] });
```

---

### UX note

Free users can still *read* all 3 of their existing conversations.
They just can't start a 4th. The gate goes on new conversation creation,
not on viewing history. This is the right call — don't take away what
they already have.

---

---

## Part 2 — CPI → Prediction → Hypothetical Strategy loop

### What Yiwen described

After a user submits a CPI prediction in Probability Lab, surface a 
follow-on: "Based on your macro view, here's how that thesis maps to a 
hypothetical portfolio." Connects prediction markets to investment 
strategy in one coherent flow.

---

### The insight that makes this work

CPI outcomes map cleanly to asset class behavior:

| CPI outcome | Macro implication | Favored assets |
|-------------|-------------------|----------------|
| Higher than expected | Inflation persists → Fed stays hawkish | TIPS, commodities, energy, short duration bonds |
| In line with expectations | Soft landing narrative intact | Balanced/index, moderate growth |
| Lower than expected | Disinflation → Fed may cut | Long duration bonds, growth stocks, REITs |

The AI already knows the user's archetype and risk tolerance from onboarding.
Combining those two signals (macro view + personal profile) into a strategy
is a genuinely useful output — not a generic recommendation.

---

### Architecture

No new DB models needed. This is a prompt layer on top of existing 
infrastructure. The flow:

```
User submits CPI prediction (existing Probability Lab flow)
         ↓
POST /api/probability/predictions  ← already exists
         ↓
Response includes: predicted value, market consensus, bias feedback
         ↓  [NEW]
Frontend shows "See how your CPI view affects your portfolio →" CTA
         ↓  [NEW]
POST /api/probability/macro-strategy  ← new endpoint
  body: { market_id, user_prediction, market_title }
         ↓  [NEW]
AI generates hypothetical strategy based on:
  - user's CPI prediction direction (above/in-line/below)
  - user's archetype + risk tolerance (from onboarding profile)
  - asset class implications of that macro view
         ↓  [NEW]
Frontend renders MacroStrategyCard inline in Probability Lab
```

---

### Backend

**New endpoint in `backend/app/probability/router.py`:**

```python
@router.post("/macro-strategy")
async def get_macro_strategy(
    request: MacroStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: ResilientAIClient = Depends(get_ai_client),
):
    """
    Given a user's macro prediction, generate a hypothetical
    investment strategy based on that view + their archetype.
    Pro only.
    """
    if current_user.tier != "pro":
        raise HTTPException(status_code=402, detail="Pro required")

    # Fetch user profile for archetype context
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    archetype = profile.persona if profile else "Balanced Builder"
    risk = profile.risk_tolerance if profile else "moderate"

    prompt = build_macro_strategy_prompt(
        market_title=request.market_title,
        user_prediction=request.user_prediction,
        archetype=archetype,
        risk_tolerance=risk,
    )

    response = await ai_client.complete(prompt, max_tokens=600)

    return {"strategy": response}
```

**New schema in `backend/app/probability/schemas.py`:**

```python
class MacroStrategyRequest(BaseModel):
    market_id: str
    market_title: str        # e.g. "CPI YoY — March 2026"
    user_prediction: float   # the probability the user submitted
```

**The prompt `build_macro_strategy_prompt()`:**

```python
def build_macro_strategy_prompt(
    market_title: str,
    user_prediction: float,
    archetype: str,
    risk_tolerance: str,
) -> str:
    # Translate probability to directional view
    if user_prediction >= 65:
        direction = "likely to come in above expectations (inflationary)"
        implication = "persistent inflation, Fed staying hawkish longer"
    elif user_prediction <= 35:
        direction = "likely to come in below expectations (disinflationary)"
        implication = "cooling inflation, potential for Fed rate cuts"
    else:
        direction = "likely to come in roughly in line with expectations"
        implication = "a soft landing scenario with moderate growth"

    return f"""You are a financial educator helping a user understand how their 
macro prediction connects to portfolio strategy.

The user predicted: {market_title}
Their view: {direction} (probability: {user_prediction}%)
Macro implication: {implication}

The user's investor archetype: {archetype}
Their risk tolerance: {risk_tolerance}

Generate a SHORT hypothetical portfolio strategy (not financial advice) that 
reflects this macro view, adjusted for their archetype and risk tolerance.

Format your response as JSON with this exact structure:
{{
  "thesis": "One sentence macro thesis based on their prediction",
  "assets": [
    {{"name": "Asset class or ETF example", "allocation": 30, "rationale": "Why this fits the thesis"}},
    {{"name": "...", "allocation": 25, "rationale": "..."}},
    {{"name": "...", "allocation": 25, "rationale": "..."}},
    {{"name": "...", "allocation": 20, "rationale": "..."}}
  ],
  "risk_note": "One sentence on what could invalidate this thesis",
  "learning_point": "One sentence connecting this to a core investing concept"
}}

Be educational, not prescriptive. This is a learning exercise, not a 
recommendation. Keep each rationale under 15 words."""
```

---

### Frontend

**New component `components/MacroStrategyCard.tsx`:**

```tsx
"use client";

import { useState } from "react";
import { Sparkles, Loader2, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";

interface MacroStrategyCardProps {
  marketId: string;
  marketTitle: string;
  userPrediction: number;
}

interface StrategyAsset {
  name: string;
  allocation: number;
  rationale: string;
}

interface MacroStrategy {
  thesis: string;
  assets: StrategyAsset[];
  risk_note: string;
  learning_point: string;
}

export function MacroStrategyCard({
  marketId,
  marketTitle,
  userPrediction,
}: MacroStrategyCardProps) {
  const [strategy, setStrategy] = useState<MacroStrategy | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStrategy = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.post<{ strategy: string }>(
        "/probability/macro-strategy",
        { market_id: marketId, market_title: marketTitle, user_prediction: userPrediction }
      );
      const parsed: MacroStrategy = JSON.parse(res.strategy);
      setStrategy(parsed);
    } catch {
      setError("Couldn't generate strategy. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // CTA before user clicks
  if (!strategy && !isLoading) {
    return (
      <div className="mt-4 rounded-xl border border-[#00D4AA]/20 bg-[#00D4AA]/5 p-4">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-5 w-5 text-[#00D4AA] shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">
              See how your macro view affects a portfolio
            </p>
            <p className="text-xs text-gray-400 mt-0.5">
              Based on your CPI prediction + your investor profile
            </p>
          </div>
          <Button
            onClick={fetchStrategy}
            className="bg-[#00D4AA] text-[#0A1628] hover:bg-[#00F0C0] text-xs px-3 py-1.5 h-auto"
          >
            Generate
          </Button>
        </div>
        {error && <p className="text-xs text-red-400 mt-2">{error}</p>}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="mt-4 rounded-xl border border-gray-800 bg-[#111827] p-4 flex items-center gap-3">
        <Loader2 className="h-4 w-4 text-[#00D4AA] animate-spin" />
        <p className="text-sm text-gray-400">Building your macro strategy...</p>
      </div>
    );
  }

  if (!strategy) return null;

  return (
    <div className="mt-4 rounded-xl border border-[#00D4AA]/20 bg-[#111827] p-5 space-y-4">
      {/* Thesis */}
      <div className="flex items-start gap-2">
        <Sparkles className="h-4 w-4 text-[#00D4AA] shrink-0 mt-0.5" />
        <p className="text-sm text-white font-medium">{strategy.thesis}</p>
      </div>

      {/* Allocation bars */}
      <div className="space-y-2">
        {strategy.assets.map((asset) => (
          <div key={asset.name}>
            <div className="flex justify-between mb-1">
              <span className="text-xs text-gray-300">{asset.name}</span>
              <span className="text-xs text-[#00D4AA] font-medium">{asset.allocation}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-gray-800">
              <div
                className="h-1.5 rounded-full bg-[#00D4AA]"
                style={{ width: `${asset.allocation}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-0.5">{asset.rationale}</p>
          </div>
        ))}
      </div>

      {/* Risk note + learning point */}
      <div className="border-t border-gray-800 pt-3 space-y-1.5">
        <p className="text-xs text-amber-400">
          <span className="font-medium">Risk: </span>{strategy.risk_note}
        </p>
        <p className="text-xs text-gray-400">
          <span className="font-medium text-gray-300">Learn: </span>
          {strategy.learning_point}
        </p>
      </div>
    </div>
  );
}
```

**In `app/(dashboard)/probability-lab/page.tsx`**, add after the prediction
result is shown (where `showResult` state is set):

```tsx
import { MacroStrategyCard } from "@/components/MacroStrategyCard";
import { useBillingStatus } from "@/hooks/useBillingStatus";

// Inside component:
const { isPro } = useBillingStatus();

// After the showResult block that already renders bias feedback etc:
{showResult && selectedMarket && isPro && (
  <MacroStrategyCard
    marketId={selectedMarket.id}
    marketTitle={selectedMarket.title}
    userPrediction={probability}
  />
)}

{showResult && selectedMarket && !isPro && (
  <UpgradeBanner feature="macro-to-portfolio strategy insights" />
)}
```

---

### Why this works as a demo moment for Joel on 4/28

The CPI loop is the single best thing you can show in a ViableEdu meeting.
It's not just "here's a chatbot that explains investing." It's:

1. User makes a prediction about a real economic event
2. Platform shows them how wrong/right that prediction is vs. market consensus
3. Platform shows them how that macro view would translate to a real portfolio
4. Platform names the cognitive bias if they were overconfident

That's a complete learning loop — predict, compare, strategize, reflect —
in about 90 seconds. No other financial education platform does that.
Build it before 4/28.
