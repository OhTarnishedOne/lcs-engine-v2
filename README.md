# LCS Engine

**AI-powered financial education that teaches people how to invest — without the fear.**

LCS Engine combines a personalized AI tutor, risk-free paper trading with real market data, economic forecasting exercises, and AI-generated investment strategies into a single cohesive learning experience.

---

## Features

### AI Financial Tutor
A conversational AI assistant powered by Anthropic Claude (with OpenAI fallback) that adapts its tone, complexity, and teaching style based on the user's profile. A "Cautious Beginner" gets patient, analogy-rich explanations. A "Time-Pressed" learner gets concise, actionable answers. The tutor is aware of saved strategies and portfolio context so it gives personalized advice, not generic responses.

### Paper Trading
Practice buying and selling stocks with $100k in simulated capital using real-time market data from Alpaca and Polygon.io. Place market or limit orders, track open positions with live P&L, and review trade history — all with zero financial risk.

### AI-Generated Investment Strategies
Generates personalized strategies (value, growth, income, momentum, balanced, index) based on risk tolerance, goals, and experience. Each strategy includes specific asset allocations with rationale, risk analysis, and educational learning points. Compare strategies side-by-side and ask the AI to explain any aspect.

### Probability Lab
Forecast real-world economic events (Fed rate decisions, CPI, GDP, unemployment) and get scored on accuracy using Brier scores. Market consensus is hidden until after submission to prevent anchoring bias. The system detects cognitive biases like overconfidence or extreme aversion and explains how each connects to real investing behavior.

### Personalized Onboarding
A 5-section onboarding flow profiles the user's experience level, barriers, goals, risk tolerance, learning style, and time commitment. This generates a persona that drives the entire experience — from AI tutor tone to strategy recommendations to probability lab topics.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS v4, shadcn/ui |
| State | React Query v5 (server), Zustand (UI) |
| Charts | Recharts |
| Backend | FastAPI (async Python), SQLAlchemy 2.0, Alembic |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose, bcrypt) |
| AI | Anthropic Claude (primary), OpenAI GPT-4o (fallback) |
| Market Data | Alpaca Markets (paper trading), Polygon.io (quotes/search) |
| Predictions | Kalshi (economic markets, read-only) |

---

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

Open [http://localhost:3000](http://localhost:3000) to use the app.

---

## Environment Variables

### Backend (`.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Database connection string | Yes |
| `JWT_SECRET_KEY` | Random string, min 32 chars | Yes |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |
| `ALPACA_API_KEY` | Alpaca paper trading API key | Yes |
| `ALPACA_SECRET_KEY` | Alpaca paper trading secret | Yes |
| `POLYGON_API_KEY` | Polygon.io market data key | Yes |
| `OPENAI_API_KEY` | OpenAI fallback (optional) | No |
| `CORS_ORIGINS` | Allowed frontend origins | Yes |

### Frontend (`.env.local`)

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api` |

---

## Project Structure

```
lcs-engine-v2/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + CORS + lifespan
│   │   ├── settings.py      # Pydantic settings
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic + AI clients
│   │   └── database.py      # DB engine + session
│   ├── alembic/             # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # Login + register pages
│   │   ├── (dashboard)/     # All authenticated pages
│   │   └── page.tsx         # Landing page
│   ├── components/          # Shared UI components
│   ├── features/            # Feature-specific components
│   ├── lib/api/             # API client + types
│   └── stores/              # Zustand stores
└── .env.example
```

---

## API Overview

| Group | Endpoints | Description |
|-------|-----------|-------------|
| Auth | `/api/auth/*` | Register, login, token refresh |
| Onboarding | `/api/onboarding/*` | Profile questions, responses, completion |
| Chat | `/api/chat/*` | Streaming AI conversations |
| Strategies | `/api/strategies/*` | Generate, compare, explain strategies |
| Trading | `/api/trading/*` | Portfolio, orders, quotes, search |
| Probability | `/api/probability/*` | Markets, predictions, calibration |

---

## What Makes It Different

- **Profile-driven personalization** — an AI that knows your barriers, goals, and comfort level
- **Anti-anchoring design** — market consensus hidden until you commit your prediction
- **Cognitive bias detection** — surfaces overconfidence, anchoring, and extreme aversion patterns
- **Resilient AI** — automatic fallback from Claude to GPT-4o with exponential backoff
- **Learning by doing** — every feature (chat, trading, predicting, strategies) reinforces the others

---

## Deployment

### Backend — Railway

The backend deploys to [Railway](https://railway.app) using Docker with a PostgreSQL add-on.

1. Create a new Railway project and add a **PostgreSQL** service.
2. Add a service from your GitHub repo. Railway will auto-detect `railway.toml`.
3. Set these environment variables on the backend service:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Provided automatically by the Railway PostgreSQL plugin |
| `JWT_SECRET_KEY` | Random string, min 32 chars |
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `ALPACA_API_KEY` | Alpaca paper trading key |
| `ALPACA_SECRET_KEY` | Alpaca paper trading secret |
| `POLYGON_API_KEY` | Polygon.io key |
| `CORS_ORIGINS` | Your Vercel frontend URL (e.g. `https://lcs-engine.vercel.app`) |

4. Deploy. Railway builds from `backend/Dockerfile`, runs Alembic migrations on startup, then starts uvicorn.

### Frontend — Vercel

The frontend deploys to [Vercel](https://vercel.com) with zero config.

1. Import the GitHub repo in Vercel.
2. Set **Root Directory** to `frontend`.
3. Add the environment variable:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://<your-railway-backend>.up.railway.app/api` |

4. Deploy. Vercel auto-detects Next.js and builds the frontend.

---

## License

All rights reserved.
