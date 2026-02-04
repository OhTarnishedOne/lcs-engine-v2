# Project: LCS Engine Frontend Rebuild - React/Next.js + FastAPI

## ⚠️ IMPORTANT: Development Only - Do NOT Deploy
This is a rebuild for post-Feb 3rd launch. The current Streamlit app remains the production version until after the W!se demo. Build everything locally/staging only.

## Repository
- **Current Streamlit app:** https://github.com/OhTarnishedOne/LCS_Engine (branch: clean-deploy)
- **New project:** Create in a separate directory or new branch (e.g., `nextjs-rebuild`)

## Goal
Rebuild LCS Engine with a professional frontend (React/Next.js) and proper API backend (FastAPI), matching the polish of https://jrricardoroberts.com while preserving all current functionality.

---

## Architecture

```
┌─────────────────────────────────────┐
│   Next.js Frontend (React)          │
│   - Pages: Onboarding, Strategies,  │
│     Paper Trade, Probability Lab    │
│   - Tailwind CSS styling            │
│   - Mobile-responsive               │
└─────────────────┬───────────────────┘
                  │ REST API
┌─────────────────▼───────────────────┐
│   FastAPI Backend                   │
│   ├── Routers (HTTP layer only)     │
│   ├── Domain Services (business)    │
│   ├── Integrations (external APIs)  │
│   └── Repositories (data access)    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│   Database (SQLite dev → Postgres)  │
│   - Users, profiles                 │
│   - Predictions, calibration scores │
│   - Strategies, portfolios          │
└─────────────────────────────────────┘
```

### Architecture Principles
1. **Routers** handle HTTP only—request/response, validation, status codes
2. **Domain services** contain pure business logic—no HTTP, no DB imports
3. **Integrations** wrap all external APIs—easy to mock, test, swap
4. **Repositories** abstract data access—swap SQLite for Postgres without touching services

---

## Current Streamlit Features to Preserve

### 1. Onboarding
- 5-question profile quiz
- Personalized recommendations based on answers
- Store user profile

### 2. Strategies
- AI-generated strategy recommendations
- Strategy details and explanations
- Comparison tools

### 3. Paper Trade
- Simulated trading environment
- Portfolio tracking
- Alpaca paper trading integration

### 4. Probability Lab (AI Agent)
- Metaculus integration (primary)
- Kalshi integration (fallback, exclude sports)
- Prediction exercises with probability slider
- Instant feedback comparing to community forecast
- Calibration scoring (Brier score)
- Cognitive bias detection and explanation
- Session tracking and progress
- Dashboard with charts

### 5. AI Chat
- Claude-powered Q&A
- Context-aware responses
- Streaming responses

---

## Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui
- **Charts:** Recharts
- **State:** React Query (server state) + Zustand (UI state only)
- **Forms:** React Hook Form + Zod validation

### Backend
- **Framework:** FastAPI
- **Auth:** JWT (python-jose)
- **Database:** SQLAlchemy 2.0 + Alembic migrations
- **Dev DB:** SQLite
- **Prod DB:** PostgreSQL
- **AI:** Anthropic Claude SDK
- **APIs:** Alpaca, Polygon, Metaculus, Kalshi

### Development
- **Package manager:** pnpm (frontend), pip + requirements.txt (backend)
- **Environment:** .env files (never commit)
- **Containers:** docker-compose for local dev

---

## File Structure

```
lcs-engine-v2/
├── README.md
├── docker-compose.yml
├── .gitignore
├── .env.example
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # env + settings (pydantic-settings)
│   │   ├── database.py                # SQLAlchemy engine/session
│   │   ├── deps.py                    # auth + db dependency injection
│   │   │
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── errors.py              # shared HTTP exceptions
│   │   │   ├── logging.py             # structured logging setup
│   │   │   └── schemas.py             # base response schemas
│   │   │
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/auth/* endpoints
│   │   │   ├── schemas.py             # request/response models
│   │   │   └── utils.py               # JWT creation/validation
│   │   │
│   │   ├── users/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/users/* endpoints
│   │   │   └── schemas.py
│   │   │
│   │   ├── probability/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/probability/* endpoints
│   │   │   ├── schemas.py
│   │   │   └── agent.py               # agentic orchestration logic
│   │   │
│   │   ├── strategies/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/strategies/* endpoints
│   │   │   └── schemas.py
│   │   │
│   │   ├── trading/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/trading/* endpoints
│   │   │   └── schemas.py
│   │   │
│   │   ├── chat/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # /api/chat/* endpoints
│   │   │   └── schemas.py
│   │   │
│   │   ├── domain/                    # PURE business logic (no HTTP, no DB imports)
│   │   │   ├── __init__.py
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py         # user profile logic
│   │   │   ├── probability/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service.py         # prediction logic
│   │   │   │   └── calibration.py     # Brier score, bias detection
│   │   │   ├── strategies/
│   │   │   │   ├── __init__.py
│   │   │   │   └── service.py         # strategy generation logic
│   │   │   └── trading/
│   │   │       ├── __init__.py
│   │   │       └── service.py         # portfolio/order logic
│   │   │
│   │   ├── integrations/              # External APIs ONLY (easy to mock)
│   │   │   ├── __init__.py            # re-export all clients
│   │   │   ├── metaculus.py           # Metaculus API client
│   │   │   ├── kalshi.py              # Kalshi API client
│   │   │   ├── alpaca.py              # Alpaca trading client
│   │   │   ├── polygon.py             # Polygon market data client
│   │   │   └── anthropic.py           # Claude AI client
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── models/                # SQLAlchemy ORM models
│   │       │   ├── __init__.py        # re-export all models
│   │       │   ├── user.py
│   │       │   ├── profile.py
│   │       │   ├── prediction.py
│   │       │   ├── strategy.py
│   │       │   └── portfolio.py
│   │       └── repository/            # Data access layer
│   │           ├── __init__.py
│   │           ├── base.py            # generic CRUD base
│   │           ├── user_repo.py
│   │           ├── profile_repo.py
│   │           ├── prediction_repo.py
│   │           └── strategy_repo.py
│   │
│   ├── alembic/
│   │   ├── versions/                  # migration files
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                # pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_probability.py
│   │   └── test_integrations/
│   │       ├── test_metaculus.py
│   │       └── test_kalshi.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                 # app shell, providers
│   │   ├── page.tsx                   # landing page
│   │   │
│   │   ├── (auth)/                    # auth route group
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   │
│   │   ├── onboarding/page.tsx
│   │   ├── strategies/page.tsx
│   │   ├── paper-trade/page.tsx
│   │   ├── probability-lab/page.tsx
│   │   └── chat/page.tsx
│   │
│   ├── components/
│   │   ├── ui/                        # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── slider.tsx
│   │   │   └── ...
│   │   └── layout/
│   │       ├── header.tsx
│   │       ├── nav.tsx
│   │       ├── footer.tsx
│   │       └── sidebar.tsx
│   │
│   ├── features/                      # domain-based UI logic
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   │   ├── login-form.tsx
│   │   │   │   └── register-form.tsx
│   │   │   ├── hooks/
│   │   │   │   └── use-auth.ts
│   │   │   └── types.ts
│   │   │
│   │   ├── onboarding/
│   │   │   ├── components/
│   │   │   │   ├── quiz-step.tsx
│   │   │   │   └── progress-bar.tsx
│   │   │   ├── hooks/
│   │   │   │   └── use-onboarding.ts
│   │   │   └── constants.ts           # quiz questions
│   │   │
│   │   ├── probability/
│   │   │   ├── components/
│   │   │   │   ├── question-card.tsx
│   │   │   │   ├── probability-slider.tsx
│   │   │   │   ├── feedback-display.tsx
│   │   │   │   └── calibration-chart.tsx
│   │   │   ├── hooks/
│   │   │   │   ├── use-questions.ts
│   │   │   │   └── use-predictions.ts
│   │   │   └── types.ts
│   │   │
│   │   ├── strategies/
│   │   │   ├── components/
│   │   │   │   ├── strategy-card.tsx
│   │   │   │   └── strategy-detail.tsx
│   │   │   └── hooks/
│   │   │       └── use-strategies.ts
│   │   │
│   │   ├── trading/
│   │   │   ├── components/
│   │   │   │   ├── portfolio-summary.tsx
│   │   │   │   ├── position-list.tsx
│   │   │   │   └── order-form.tsx
│   │   │   └── hooks/
│   │   │       └── use-trading.ts
│   │   │
│   │   └── chat/
│   │       ├── components/
│   │       │   ├── chat-window.tsx
│   │       │   ├── message-bubble.tsx
│   │       │   └── input-bar.tsx
│   │       └── hooks/
│   │           └── use-chat.ts
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts              # fetch wrapper with auth
│   │   │   ├── endpoints.ts           # API route constants
│   │   │   └── types.ts               # shared API types
│   │   ├── utils.ts                   # cn(), formatters, etc.
│   │   └── constants.ts
│   │
│   ├── stores/                        # Zustand (UI-only state)
│   │   └── ui-store.ts                # sidebar open, theme, etc.
│   │
│   ├── styles/
│   │   └── globals.css                # Tailwind imports + custom
│   │
│   ├── middleware.ts                  # auth route protection
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── package.json
│   └── pnpm-lock.yaml
│
└── docs/
    ├── architecture.md                # this document, expanded
    ├── api.md                         # endpoint documentation
    └── decisions.md                   # ADRs (architecture decision records)
```

---

## API Endpoints

### Auth
```
POST /api/auth/register        # Create account
POST /api/auth/login           # Get JWT tokens
POST /api/auth/refresh         # Refresh access token
GET  /api/auth/me              # Current user info
```

### Users
```
GET  /api/users/profile        # Get user profile
PUT  /api/users/profile        # Update profile
POST /api/users/onboarding     # Save quiz answers, mark complete
```

### Strategies
```
GET  /api/strategies           # List strategies for user
GET  /api/strategies/{id}      # Strategy detail
POST /api/strategies/generate  # AI-generate new strategy
```

### Trading
```
GET  /api/trading/portfolio    # Portfolio summary
GET  /api/trading/positions    # Current positions
POST /api/trading/order        # Place paper trade
GET  /api/trading/history      # Order history
```

### Probability Lab
```
GET  /api/probability/questions          # Fetch from Metaculus/Kalshi
GET  /api/probability/question/{id}      # Single question detail
POST /api/probability/predict            # Submit prediction
GET  /api/probability/history            # User's prediction history
GET  /api/probability/calibration        # Brier score, calibration curve
GET  /api/probability/session            # Current session state
POST /api/probability/session/new        # Start new session
```

### Chat
```
POST /api/chat                 # Send message, get AI response
GET  /api/chat/history         # Conversation history
DELETE /api/chat/history       # Clear history
```

---

## Database Schema

### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### profiles
```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    risk_tolerance VARCHAR(20),          -- conservative, moderate, aggressive
    investment_horizon VARCHAR(20),      -- short, medium, long
    experience_level VARCHAR(20),        -- beginner, intermediate, advanced
    goals JSONB,                         -- array of goal strings
    interests JSONB,                     -- for probability lab topics
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### predictions
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source VARCHAR(20) NOT NULL,         -- 'metaculus' or 'kalshi'
    question_id VARCHAR(100) NOT NULL,
    question_title TEXT NOT NULL,
    category VARCHAR(50),
    user_probability FLOAT NOT NULL,     -- 0.0 to 1.0
    market_probability FLOAT NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    outcome BOOLEAN,                     -- NULL until resolved
    brier_score FLOAT,                   -- calculated on resolution
    
    INDEX idx_predictions_user (user_id),
    INDEX idx_predictions_resolved (resolved)
);
```

### strategies
```sql
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50),           -- value, growth, dividend, etc.
    parameters JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### portfolios
```sql
CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    cash_balance DECIMAL(15, 2) DEFAULT 100000.00,  -- paper trading start
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### positions
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    quantity DECIMAL(15, 6) NOT NULL,
    avg_cost DECIMAL(15, 4) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(portfolio_id, symbol)
);
```

### orders
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    side VARCHAR(4) NOT NULL,            -- 'buy' or 'sell'
    quantity DECIMAL(15, 6) NOT NULL,
    order_type VARCHAR(10) NOT NULL,     -- 'market' or 'limit'
    limit_price DECIMAL(15, 4),
    status VARCHAR(20) NOT NULL,         -- pending, filled, cancelled
    filled_price DECIMAL(15, 4),
    filled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Design Guidelines

Reference: https://jrricardoroberts.com

### Colors
- **Primary:** Blue (#2563eb / Tailwind blue-600)
- **Background:** White (#ffffff) / Slate-50 (#f8fafc)
- **Text:** Slate-900 (#0f172a) / Slate-600 (#475569)
- **Accent:** Emerald for success, Amber for warnings, Rose for errors

### Typography
- **Font:** Inter (or system font stack)
- **Headings:** Bold, good hierarchy (text-3xl → text-xl → text-lg)
- **Body:** text-base, leading-relaxed

### Layout
- **Max width:** max-w-6xl for content, max-w-md for forms
- **Spacing:** Generous whitespace (p-6, gap-6, space-y-8)
- **Cards:** Rounded corners (rounded-xl), subtle shadows

### Components
- **Buttons:** Rounded, clear hover states
- **Inputs:** Clean borders, focus rings
- **Cards:** White background, subtle border or shadow

### Mobile-first
- Start with mobile layout, expand for larger screens
- Collapsible sidebar/nav on mobile
- Touch-friendly targets (min 44px)

---

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=sqlite:///./lcs_dev.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/lcs  # prod

# Auth
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# External APIs
ANTHROPIC_API_KEY=sk-ant-...
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
POLYGON_API_KEY=...

# Optional
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## Development Commands

### First-time setup
```bash
# Clone and enter directory
git clone <repo>
cd lcs-engine-v2

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp ../.env.example .env   # edit with your keys
alembic upgrade head      # run migrations

# Frontend setup
cd ../frontend
pnpm install
cp .env.example .env.local  # edit API URL if needed
```

### Running locally
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
pnpm dev
```

### With Docker
```bash
docker-compose up --build
```

### Database migrations
```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Running tests
```bash
cd backend
pytest -v
```

---

## Implementation Priority

### Phase 1: Backend Foundation (Week 1)
1. FastAPI project structure with all folders
2. Config, database setup, deps.py
3. User and Profile models + migrations
4. Auth endpoints (register, login, JWT refresh)
5. Basic user/profile endpoints

### Phase 2: Core Integrations (Week 2)
1. Port Metaculus client to integrations/
2. Port Kalshi client to integrations/
3. Calibration service in domain/probability/
4. Prediction model + repository
5. Probability Lab endpoints

### Phase 3: Trading & Chat (Week 2-3)
1. Port Alpaca client to integrations/
2. Portfolio/Position/Order models
3. Trading endpoints
4. Anthropic client for chat
5. Chat endpoints with streaming

### Phase 4: Frontend Foundation (Week 3)
1. Next.js project with Tailwind + shadcn/ui
2. API client with auth handling
3. Auth pages (login, register)
4. App layout (nav, header, sidebar)
5. Protected route middleware

### Phase 5: Frontend Features (Week 4-5)
1. Onboarding flow (quiz → profile)
2. Strategies page
3. Probability Lab (slider, feedback, charts)
4. Paper Trade interface
5. Chat interface

### Phase 6: Polish (Week 6)
1. Loading states, error boundaries
2. Mobile responsiveness pass
3. Animations (Framer Motion optional)
4. E2E testing (Playwright optional)
5. Documentation cleanup

---

## Key Implementation Notes

### Backend: integrations/__init__.py
```python
"""Re-export all integration clients for easy imports."""
from .metaculus import MetaculusClient
from .kalshi import KalshiClient
from .alpaca import AlpacaClient
from .polygon import PolygonClient
from .anthropic import ClaudeClient

__all__ = [
    "MetaculusClient",
    "KalshiClient", 
    "AlpacaClient",
    "PolygonClient",
    "ClaudeClient",
]
```

### Backend: deps.py pattern
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .database import SessionLocal
from .auth.utils import verify_token

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(security),
    db: Session = Depends(get_db)
):
    payload = verify_token(token.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    # fetch and return user
    ...
```

### Frontend: API client pattern
```typescript
// lib/api/client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options?.headers,
    };

    const res = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      throw new Error(await res.text());
    }

    return res.json();
  }
}

export const api = new ApiClient();
```

---

## Reminders

- ⚠️ **DO NOT deploy to production until after Feb 3rd**
- Keep Streamlit app running as primary until cutover
- Test thoroughly before any public release
- This is a **rebuild**, not a migration—start fresh, port logic
- Commit often with clear messages
- Write tests as you go, especially for domain services
