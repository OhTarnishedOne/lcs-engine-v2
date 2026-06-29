# CODEX.md
## OpenAI Codex — Dev Environment

### Stack
- Backend: FastAPI (Python 3.12) at backend/, port 8000
- Frontend: Next.js at frontend/, port 3000
- DB: SQLite (dev) / PostgreSQL (prod, Railway)
- Demo: Static Next.js at demo/, port 3001 (install on demand)

### Setup
1. Create backend venv if absent: python3.12 -m venv backend/venv
2. Install backend deps: pip install -r backend/requirements.txt
3. Run migrations: cd backend && ./venv/bin/alembic upgrade head
4. Install frontend deps: npm --prefix frontend install

### Running
- Backend: cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000
- Frontend: cd frontend && npm run dev

### Env files
Gitignored. Backend boots without backend/.env using SQLite defaults. Frontend defaults to localhost:8000 without frontend/.env.local. See .env.example for all keys.

### API key degradation
Without keys: AI chat, tutor, and strategy generation degrade gracefully. Auth, onboarding tap screens, and Probability Lab (DB-seeded markets) work fully.

### Tests
cd backend && ./venv/bin/python -m pytest
Expected: 5 pre-existing failures in tests/test_chat.py (mock/router mismatch on get_ai_client). All other suites pass.

### Lint
cd frontend && npm run lint
Pre-existing lint errors in repo source are expected.

### Key files
- backend/app/main.py — FastAPI entrypoint
- backend/app/probability/calibration.py — Calibration Score engine
- frontend/app/(dashboard)/ — all dashboard pages
- frontend/components/CalibrationEngineLoop.tsx — DI Engine loop UI
- AGENTS.md — Cursor Cloud specific instructions
- CLAUDE.md — Claude Code specific instructions
