# LCS Engine

**The decision intelligence platform that trains people to know how confident they should have been.**

LCS Engine measures, trains, and improves financial decision-making under uncertainty. At its core is the **Calibration Score** (patent pending) — a metric that grades your *reasoning process*, not your outcomes. You are not being graded on whether you guessed right. You are being trained to know how confident you should have been.

The platform runs an active **Decide → Score → Diagnose → Improve** loop: users make probabilistic forecasts on real economic events, get scored on calibration using Brier scoring, receive diagnosis of cognitive biases in their reasoning, and improve through a personalized AI tutor, risk-free paper trading, and AI-generated strategies.

## Features

### Calibration Score & Gamification Engine *(patent pending)*
The measurement layer. Every resolved prediction feeds a Brier scoring engine that rolls into a user-facing Calibration Score, score families (progression tiers based on demonstrated calibration), and a badge system that rewards well-calibrated reasoning — not bold guessing. Outcomes resolve against external market data feeds, so scores are grounded in reality, not self-report. Backed by 119 passing tests.

### Probability Lab
Forecast real-world economic events (Fed rate decisions, CPI, GDP, unemployment) and get scored on accuracy. Market consensus is hidden until after submission to prevent anchoring bias. The system detects cognitive biases like overconfidence or extreme aversion and explains how each connects to real investing behavior.

### AI Decision Tutor
A conversational AI assistant powered by Anthropic Claude (with OpenAI fallback) that adapts its tone, complexity, and teaching style to the user's profile. The tutor is aware of the user's calibration history, saved strategies, and portfolio context — it gives personalized coaching, not generic responses.

### Paper Trading
Practice buying and selling stocks with $100k in simulated capital using real-time market data from Alpaca and Polygon.io. Place market or limit orders, track open positions with live P&L, and review trade history — decisions with feedback, without financial risk.

### AI-Generated Investment Strategies
Generates personalized strategies (value, growth, income, momentum, balanced, index) based on risk tolerance, goals, and experience. Each strategy includes specific asset allocations with rationale, risk analysis, and educational learning points.

### Personalized Onboarding
A 5-section onboarding flow profiles the user's experience level, barriers, goals, risk tolerance, learning style, and time commitment. This generates a disposition persona that drives the entire experience — with the architecture designed to evolve toward behavioral fingerprinting through observed micro-decisions.

## The Decision Intelligence Framework

| Layer | What it does | Where it lives |
|---|---|---|
| **Disposition** | Archetype onboarding, risk profiling | Onboarding flow |
| **Reasoning** | Probability Lab + Calibration Score | Prediction & scoring engine |
| **Application** | Paper trading + AI tutor | Trading & chat |
| **Memory** | Decision journal + pattern aggregation | History & diagnostics |

The architecture is domain-agnostic — calibration measurement applies to any decision domain — while the current UI focuses on investing.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, shadcn/ui |
| State | React Query v5 (server), Zustand (UI) |
| Charts | Recharts |
| Backend | FastAPI (async Python), SQLAlchemy 2.0, Alembic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose, bcrypt) |
| AI | Anthropic Claude (primary), OpenAI GPT-4o (fallback) |
| Market Data | Alpaca Markets (paper trading), Polygon.io (quotes/search) |
| Predictions | Kalshi (economic markets, read-only) |
| Billing | Stripe |

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- API keys for: Anthropic, Alpaca (paper), Polygon.io
- Optional: OpenAI (fallback AI), Kalshi (prediction markets)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env with your API keys and a secure JWT secret

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local if your backend runs on a different URL

# Start dev server
npm run dev
```

Open http://localhost:3000 to use the app.

### Running Tests

```bash
cd backend
pytest
```

The gamification engine alone carries 119 tests covering Brier scoring, score family transitions, and badge evaluation.

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|---|---|---|
| DATABASE_URL | Database connection string | Yes |
| JWT_SECRET_KEY | Random string, min 32 chars | Yes |
| ANTHROPIC_API_KEY | Anthropic Claude API key | Yes |
| ALPACA_API_KEY | Alpaca paper trading API key | Yes |
| ALPACA_SECRET_KEY | Alpaca paper trading secret | Yes |
| POLYGON_API_KEY | Polygon.io market data key | Yes |
| OPENAI_API_KEY | OpenAI fallback (optional) | No |
| CORS_ORIGINS | Allowed frontend origins | Yes |

### Frontend (.env.local)

| Variable | Description | Default |
|---|---|---|
| NEXT_PUBLIC_API_URL | Backend API URL | http://localhost:8000/api |

## Project Structure

```
lcs-engine-v2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + CORS + lifespan
│   │   ├── settings.py          # Pydantic settings
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic + AI clients
│   │   │   └── gamification/    # Brier engine, score families, badges
│   │   └── database.py          # DB engine + session
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Test suites (pytest)
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── (auth)/              # Login + register pages
│   │   ├── (dashboard)/         # All authenticated pages
│   │   └── page.tsx             # Landing page
│   ├── components/              # Shared UI components
│   ├── features/                # Feature-specific components
│   ├── lib/api/                 # API client + types
│   └── stores/                  # Zustand stores
├── stripe_integration/          # Billing
├── demo/                        # Demo assets
└── .env.example
```

## API Overview

| Group | Endpoints | Description |
|---|---|---|
| Auth | /api/auth/* | Register, login, token refresh |
| Onboarding | /api/onboarding/* | Profile questions, responses, completion |
| Chat | /api/chat/* | Streaming AI conversations |
| Strategies | /api/strategies/* | Generate, compare, explain strategies |
| Trading | /api/trading/* | Portfolio, orders, quotes, search |
| Probability | /api/probability/* | Markets, predictions, calibration |
| Gamification | /api/gamification/* | Calibration score, score history, badges, evaluation |

## What Makes It Different

- **Calibration over outcomes** — the score grades reasoning quality, not luck; patent pending on the methodology
- **Grounded resolution** — predictions resolve against external market data feeds, not self-report
- **Anti-anchoring design** — market consensus hidden until you commit your prediction
- **Cognitive bias detection** — surfaces overconfidence, anchoring, and extreme aversion patterns
- **Profile-driven personalization** — an AI that knows your barriers, goals, and calibration history
- **Resilient AI** — automatic fallback from Claude to GPT-4o with exponential backoff
- **Learning by doing** — every feature (predicting, trading, chatting, strategizing) reinforces the loop

## Deployment

### Backend — Railway

The backend deploys to Railway using Docker with a PostgreSQL add-on.

1. Create a new Railway project and add a PostgreSQL service.
2. Add a service from your GitHub repo. Railway will auto-detect `railway.toml`.
3. Set these environment variables on the backend service:

| Variable | Value |
|---|---|
| DATABASE_URL | Provided automatically by the Railway PostgreSQL plugin |
| JWT_SECRET_KEY | Random string, min 32 chars |
| ANTHROPIC_API_KEY | Your Anthropic API key |
| ALPACA_API_KEY | Alpaca paper trading key |
| ALPACA_SECRET_KEY | Alpaca paper trading secret |
| POLYGON_API_KEY | Polygon.io key |
| CORS_ORIGINS | Your Vercel frontend URL (e.g. https://lcs-engine.vercel.app) |

4. Deploy. Railway builds from `backend/Dockerfile`, runs Alembic migrations on startup, then starts uvicorn.

### Frontend — Vercel

The frontend deploys to Vercel with zero config.

1. Import the GitHub repo in Vercel.
2. Set Root Directory to `frontend`.
3. Add the environment variable:

| Variable | Value |
|---|---|
| NEXT_PUBLIC_API_URL | https://<your-railway-backend>.up.railway.app/api |

4. Deploy. Vercel auto-detects Next.js and builds the frontend.

## Intellectual Property

The Calibration Score methodology — including the Brier scoring engine, score family system, behavioral fingerprinting, and dynamic risk profiling — is patent pending. All rights reserved.
