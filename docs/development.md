# Developer Onboarding Guide

Welcome to the FinGuard AI team! We prioritize developer experience and high velocity.

## Code Style Guide
- **Python**: Enforced fully via `Ruff` and `Black`. All code sits internally in PEP 8 standards cleanly avoiding syntax fragmentation.
- **JavaScript/React**: Enforced natively via `Prettier`. React hook components should rely strictly on Context and Props avoiding deep native object mutations.

## Environment Layouts
All sensitive parameters live outside git via `.env`. Generate an `.env` strictly using `.env.example` as your standard.

## Running the Stack
The easiest way to initialize instances is Docker Compose:
```bash
make build
make dev
```
Wait approximately ~15s for Alembic scripts to boot and map relations cleanly over postgres.

### Running Without Docker
1. Start local Postgres, Redis.
2. Ensure Python 3.11+ is active.
3. Install: `pip install -r requirements.txt`.
4. Run DB Migrations: `alembic upgrade head`.
5. Frontend install: `npm install && npm run dev`
6. Backend boot: `uvicorn backend.main:app --reload`

## Debugging Tips
- Trace SQL bounds setting `echo=True` inside `backend/database.py` mapping specific queries.
- Check Prometheus endpoints directly at `localhost:8000/metrics`.
