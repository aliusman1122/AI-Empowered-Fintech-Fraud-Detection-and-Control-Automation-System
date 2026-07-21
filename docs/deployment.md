# Deployment Guide (Hardened Production)

## Infrastructure Prerequisites
- Docker & Docker Compose v2+
- Ports 8000 (Backend), 5173 (Frontend), 3000 (Grafana), 9090 (Prometheus), 5000 (MLFlow), 5678 (N8N) available.

## Quick Start
1. Ensure your `.env` contains explicit strong hexadecimal secrets. Never use `admin123` defaults.
2. Build network and services:
```bash
docker-compose up --build -d
```
3. Run Alembic Database tracking migrations:
```bash
docker exec fraud_backend alembic upgrade head
```
4. Verify Health Checks:
```bash
docker ps
# Ensure all services report (healthy)
```

## Scaling
- Redis handles high IO throughput async connections.
- MLflow targets its dedicated PostgreSQL database internally to strictly avoid SQLite data-corruption during concurrent transaction inferences.
- Frontend uses parameterised Nginx deployment via dist generation (`Dockerfile` Stage 2).
