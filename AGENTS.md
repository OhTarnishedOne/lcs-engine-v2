# AGENTS.md

## Cursor Cloud specific instructions

Standard commands and stack details live in `README.md` and `CLAUDE.md`; this section only captures non-obvious caveats for running this repo in the Cloud VM.

### Services
- **Backend** — FastAPI at `backend/`, run on port 8000.
- **Frontend** — Next.js app at `frontend/`, run on port 3000 (the user-facing product).
- `demo/` is a separate static marketing demo (Next.js, port 3001) and is NOT installed by the update script; install it on demand with `npm --prefix demo install` if you need it.

### Python venv (important)
- The backend runs in a virtualenv at `backend/venv` created by the startup update script. There is no `activate` step needed: invoke tools directly, e.g. `backend/venv/bin/uvicorn ...`, `backend/venv/bin/pytest`, `backend/venv/bin/alembic ...`. Do not use the system `python3`/`pip` for backend work.

### First-run setup not handled by the update script
- The update script only installs dependencies. Before starting the backend the first time, create/upgrade the SQLite schema: `cd backend && ./venv/bin/alembic upgrade head`. The dev DB is `backend/lcs_dev.db` (gitignored), so it must be migrated in a fresh checkout.
- Env files are gitignored and may be absent on a fresh VM. Backend settings default to local SQLite + a placeholder JWT secret, so the API boots without `backend/.env`. The frontend API client defaults to `http://localhost:8000/api`, so `frontend/.env.local` is also optional for the default localhost setup.

### Running (dev mode)
- Backend: `cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`

### Missing API keys = expected degradation (not bugs)
- No external API keys are configured by default. With keys absent:
  - The **onboarding AI chat step and the tutor chat render blank / hang** (the AI client never responds). This is expected — the tap-screen onboarding, auth/register/login, and Probability Lab (DB-seeded markets) still work fully end to end.
  - Strategy generation needs `ANTHROPIC_API_KEY`; registered-user paper trading + quotes need `ALPACA_API_KEY`/`ALPACA_SECRET_KEY`/`POLYGON_API_KEY`.
- To exercise AI/trading flows, set the relevant keys in `backend/.env` (see `.env.example`).

### Tests / lint caveats
- `cd backend && ./venv/bin/python -m pytest`: on a clean checkout, 5 tests in `tests/test_chat.py` fail because they override `get_anthropic_client` while `chat/router.py` depends on `get_ai_client` (`ResilientAIClient`), so the mock never applies. This is a pre-existing test/code mismatch, independent of environment setup.
- `cd frontend && npm run lint` runs but reports pre-existing lint errors/warnings in the repo source.
