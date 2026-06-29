# CLAUDE.md

## Project Overview
LCS Engine v2 — a financial literacy platform with AI-powered onboarding, chat, strategy generation, paper trading, and a probability lab.

## Stack
- **Backend:** FastAPI (Python), SQLAlchemy ORM, Alembic migrations, PostgreSQL
- **Frontend:** Next.js 16 (App Router), TypeScript, TanStack Query, Framer Motion, Tailwind CSS
- **Infra:** Backend on Railway, Frontend on Vercel (www.lcsengine.com)
- **AI:** Anthropic Claude via `ResilientAIClient` wrapper

## Repository Layout
```
backend/
  app/
    main.py              # FastAPI app with lifespan
    database.py           # SQLAlchemy engine/session
    settings.py           # Config via env vars
    deps.py               # FastAPI dependencies (get_db, get_current_user, get_ai_client)
    db/models/            # SQLAlchemy models
    auth/                 # JWT auth (register, login, refresh, forgot/reset password)
    onboarding/           # Tap screens + chat onboarding
    chat/                 # AI chat conversations
    strategies/           # AI-generated investment strategies
    trading/              # Paper trading (Alpaca integration)
    probability/          # Prediction markets + calibration
    admin/                # Stats endpoints (no auth)
    analytics/            # Event tracking
    config/               # Onboarding questions config
  alembic/versions/       # Migrations (001-012, sequential IDs)
frontend/
  app/(auth)/             # Public auth pages (login, register, forgot-password, reset-password)
  app/(dashboard)/        # Authenticated pages (onboarding, chat, dashboard, etc.)
  lib/api/client.ts       # API client singleton with auto token refresh
  lib/api/types.ts        # Shared TypeScript interfaces
  components/ui/          # Reusable UI components
```

## Development Commands
```bash
# Backend
cd backend && uvicorn app.main:app --reload          # Dev server
cd backend && python3 -m pytest                       # Tests (113 tests)
cd backend && alembic upgrade head                    # Run migrations (local only)
cd backend && alembic revision -m "description"       # New migration

# Frontend
cd frontend && npm run dev                            # Dev server
cd frontend && npm run build                          # Production build (also type-checks)
cd frontend && npm run lint                           # ESLint
# No test suite configured
```

## Deployment
```bash
cd backend && railway up       # Deploys backend; Dockerfile auto-runs alembic upgrade head
cd frontend && vercel --prod   # Deploys frontend
```
- DB host `postgres.railway.internal` is only reachable inside Railway containers
- Cannot run migrations locally against production DB — they run automatically on deploy
- No `psql` installed locally

## Key Patterns

### SQLAlchemy JSON Columns
In-place mutation of JSON columns is NOT detected. Always copy before modifying:
```python
existing = dict(profile.some_json_col or {})
existing[key] = value
profile.some_json_col = existing
```

### Multi-Select Tap Values
Tap screens with `multiSelect: true` return `list[str]`, not `str`. Before using as a dict key:
```python
if isinstance(raw_value, list):
    raw_value = raw_value[0] if raw_value else default
```

### Frontend API Client
- Singleton at `frontend/lib/api/client.ts` (`export const api = new ApiClient()`)
- Auto token refresh on 401
- SSE streaming endpoints (`sendOnboardingChat`, `sendChatMessage`) return raw `Response`

### Onboarding Flow
Two-phase: tap screens (5 quick questions) → AI chat conversation.
- Tap screen keys: `experience_level` (single), `goals` (multi, max 3), `risk_tolerance` (single), `interests` (multi, max 4), `learning_style` (multi, max 2)
- `tap_responses` JSON column on UserProfile persists per-screen progress
- `POST /onboarding/complete-conversation` merges tap data + AI-extracted conversation data
- Mapping constants in router.py: `EXPERIENCE_LEVEL_MAP`, `LEARNING_STYLE_MAP`, `RISK_TOLERANCE_MAP`

## Migrations
Sequential numbering: `001_initial_user_profile.py` through `012_add_password_reset_tokens.py`. Use `down_revision` matching the previous number.

## Admin
- `GET /api/admin/onboarding-stats` — no auth, aggregate onboarding analytics
- No delete-user endpoint; for test cleanup, temporarily add one to admin router, deploy, run, revert

## Code Style
- Backend: Python type hints, Pydantic schemas, SQLAlchemy mapped_column style
- Frontend: TypeScript strict, functional components, TanStack Query for data fetching
- Commit messages: imperative mood, explain "why" not "what"

## Claude Code — Dev Environment

- Backend runs in a virtualenv at `backend/venv`. Always invoke via `backend/venv/bin/python`, `backend/venv/bin/pytest`, `backend/venv/bin/uvicorn` etc. Never use system `python3` for backend work.
- Before first run on a fresh checkout: `cd backend && ./venv/bin/alembic upgrade head`
- Dev DB is `backend/lcs_dev.db` (SQLite, gitignored). Production uses PostgreSQL on Railway.
- Backend starts on port 8000: `cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000`
- Frontend starts on port 3000: `cd frontend && npm run dev`
- Env files are gitignored. Backend boots without `backend/.env` (defaults to SQLite + placeholder JWT). Frontend defaults to `http://localhost:8000/api` without `frontend/.env.local`.
- Missing API keys cause expected degradation: AI chat/tutor renders blank, strategy generation fails. Auth, onboarding, and Probability Lab work fully without keys.
- Test caveats: 5 tests in `backend/tests/test_chat.py` fail pre-existing due to mock targeting `get_anthropic_client` while router depends on `get_ai_client`. Not an environment issue.
- `npm run lint` reports pre-existing errors in repo source. Expected, not introduced by Claude Code sessions.
- `demo/` is a separate static Next.js site (port 3001). Not installed by default — run `npm --prefix demo install` on demand.
