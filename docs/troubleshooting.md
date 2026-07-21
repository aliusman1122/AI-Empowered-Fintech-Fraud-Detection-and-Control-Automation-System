# Troubleshooting Guide

### 1. Database Mismatches
If you see `sqlalchemy.exc.ProgrammingError: column "reason_codes" of relation "transactions" does not exist`, the database schema is out of sync.
**Fix Phase:** Run `docker exec fraud_backend alembic upgrade head` to coerce sync. Ensure `alembic` reflects JSONB changes.

### 2. Vite API Base Disconnections
If the frontend UI shows **"Network Error"** while making fetches in production, verify Vite proxy and base URL routing.
**Fix Phase:** Ensure `VITE_API_BASE_URL` is set correctly in `.env.production` (usually `/api/v1` for NGINX proxy arrays) and Vite configs utilize `changeOrigin: true` over `docker` bridging. 

### 3. n8n Invalid Trigger Drops
If n8n does not fire alerts:
**Fix Phase:** Check `backend/core/config.py` for `N8N_WEBHOOK_URL` dialing `http://n8n:5678/`. Also ensure the `n8n/workflows/FraudAlertWorkflow.json` was properly imported into the n8n application via the UI.

### 4. MLFlow Tracking Loss
**Fix Phase:** We hardened MLFlow to use PostgreSQL (`mlflow` table in `postgres:5432`). If tracking errors manifest, ensure `mlflow` service `depends_on: postgres` and `postgres_init.sql` actually created the `mlflow` database.
