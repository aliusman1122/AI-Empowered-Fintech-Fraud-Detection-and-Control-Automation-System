import os
from pathlib import Path

root = Path(r"c:\D_volume\FYP\Projects\AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System")
(root / "docs").mkdir(exist_ok=True)
(root / "docker").mkdir(exist_ok=True)

readme_content = """# AI-Empowered Fintech Fraud Detection and Control Automation System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) 
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green?logo=fastapi) 
![React](https://img.shields.io/badge/React-18.0-blue?logo=react)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![n8n](https://img.shields.io/badge/n8n-Automation-orange?logo=n8n)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)

An enterprise-grade, real-time automated fraud detection and risk mitigation engine designed for modern financial technology.

## 🏛️ System Architecture

```mermaid
graph TD
    User([End User / Dashboard]) --> API[FastAPI Core Engine]
    API --> ML[ML Inference Model]
    ML -->|Risk < 0.3| DB[(Database)]
    ML -->|Risk >= 0.3| N8N[n8n Automation]
    N8N --> Email[Send Alert Email]
    Email --> |Approve/Reject| Webhook[n8n Webhook]
    Webhook --> API
```

## ✨ Features
- 🧠 **Machine Learning Engine**: Real-time fraud probability scoring using Random Forest models.
- ⚡ **High-Performance API**: Asynchronous endpoints powered by FastAPI.
- 🔐 **Robust Security**: JWT-based authentication and secure endpoints.
- 📧 **Automated Triage**: n8n-powered email alert workflows with single-click approve/reject actions.
- 📊 **Dashboard Ready**: Richly formatted statistics for unified operational oversight.
- 🐳 **Fully Containerized**: Complete Docker Compose setup for instant deployment.

## 📚 Documentation
Check the `docs/` folder for detailed guides:
- [API Reference](docs/API.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Local Setup](docs/SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)

## 📖 API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and receive JWT |
| POST | `/api/v1/transactions/predict` | Predict transaction fraud score |
| GET | `/api/v1/transactions/{id}` | Get specific transaction status |
| POST | `/api/v1/transactions/{id}/verify`| Approve or reject via Webhook |
| GET | `/api/v1/transactions/` | List all transactions |
| GET | `/api/v1/dashboard/stats` | Retrieve aggregate statistics |

## 🚀 Quick Setup
```bash
docker-compose up --build
```
"""

api_md_content = """# API Reference

## Authentication
- `POST /api/v1/auth/register` - Register a user (Payload: `email`, `password`, `full_name`)
- `POST /api/v1/auth/login` - Retrieve access token

## Transactions
- `POST /api/v1/transactions/predict`
  Predicts whether a transaction is fraudulent.
- `GET /api/v1/transactions`
  Returns all transactions, supporting limit/offset and filters.
- `GET /api/v1/transactions/{transaction_id}`
  Retrieves status details for a given transaction UUID.
- `POST /api/v1/transactions/{transaction_id}/verify`
  Action payload: `{"action": "approve"}` or `{"action": "reject"}`.

## Analytics
- `GET /api/v1/dashboard/stats`
  Returns aggregate statistics of the fraud detection performance.
"""

arch_md_content = """# Architecture Overview
This system utilizes a Service-Oriented Architecture (SOA):
- **Gateway & API**: FastAPI routes all incoming requests.
- **Inference Layer**: Scikit-learn Random Forest model trained on generated behavioral data.
- **Data Layer**: SQLite/PostgreSQL used for relational mapping via SQLAlchemy ORM.
- **Automation Layer**: n8n workflow triggers webhooks for email-based Out-of-Band (OOB) verification.
"""

setup_md_content = """# Local Setup Guide
1. **Clone the repository**
2. **Create environment variables**: `cp .env.example .env` (fill in your local details).
3. **Database initialization**:
   `python -m backend.init_db`
4. **Run FastAPI**:
   `uvicorn backend.main:app --reload`
"""

contributing_md_content = """# Contributing
1. Fork the repo.
2. Create a feature branch: `git checkout -b feature/awesome-feature`
3. Commit your changes strictly following our conventional commit format (`feat:`, `fix:`, `docs:`, etc).
4. Create a Pull Request against the main branch.
"""

docker_backend_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

docker_frontend_content = """FROM node:18-alpine
WORKDIR /app
# Mock package.json since it's a placeholder
RUN echo '{"name":"fraud-dashboard","version":"1.0.0","scripts":{"start":"echo Frontend running && sleep infinity"}}' > package.json
CMD ["npm", "start"]
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1
"""

docker_compose_content = """version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/fraud_db
      - N8N_WEBHOOK_URL=http://n8n:5678/webhook/fintech-fraud-alert
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    ports:
      - "3000:3000"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=fraud_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n
      - VUE_APP_URL_BASE_API=http://localhost:5678/
      - WEBHOOK_URL=http://localhost:5678/
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5678/healthz"]
      interval: 20s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
"""

deploy_md_content = """# Deployment to Railway
1. **Login to Railway**: Sign in to your Railway.app account.
2. **Import Repository**: Connect your Github repo.
3. **Add Postgres & Redis**: Use the Railway Marketplace to provision managed DB/Cache.
4. **Environment Variables**: Add your `DATABASE_URL` and `JWT_SECRET_KEY` into the Railway Dashboard.
5. **Auto-Deploy**: Commit to your main branch, and Railway will use the `docker-compose.yml` to automatically build your instances.
"""

(root / "README.md").write_text(readme_content, "utf-8")
(root / "docs" / "API.md").write_text(api_md_content, "utf-8")
(root / "docs" / "ARCHITECTURE.md").write_text(arch_md_content, "utf-8")
(root / "docs" / "SETUP.md").write_text(setup_md_content, "utf-8")
(root / "docs" / "CONTRIBUTING.md").write_text(contributing_md_content, "utf-8")
(root / "docs" / "DEPLOYMENT.md").write_text(deploy_md_content, "utf-8")
(root / "docker" / "Dockerfile.backend").write_text(docker_backend_content, "utf-8")
(root / "docker" / "Dockerfile.frontend").write_text(docker_frontend_content, "utf-8")
(root / "docker-compose.yml").write_text(docker_compose_content, "utf-8")
print("Phase 9 & 10 assets created.")
