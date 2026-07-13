---

# 🛡️ FinGuard: AI-Empowered Fintech Fraud Detection & Control Automation System

An enterprise-grade, real-time automated fraud detection and risk mitigation engine designed for modern financial technology and core banking layers.

🎓 **Final Year Project / Portfolio Presentation**
* 👤 **Author**: Mohammad Usman
* 🏛️ **University**: Minhaj University Lahore
* 👔 **Supervisor**: Dr. Gulzar Ahmad
* 📅 **Academic Year**: 2026

---

## 🎯 Project Overview & Vision
Modern financial transaction systems process millions of orders per second where standard static rules fail against evolving fraud patterns. **FinGuard** bridges this gap by injecting an intelligent machine learning inference layer between transaction ingestion and bank processing, coupled with an automated incident management pipeline.

### 🔄 Core Automation Control Loop
* **Ingestion Phase**: Transactions are initiated via the real-time financial web dashboard.
* **AI Scoring Model**: A predictive machine learning pipeline calculates an explicit fraud probability score.
* **Threshold-based Triage**:
  * `Score < 0.35`: **Auto-Approved** immediately. Bank core system executes the ledger release.
  * `Score ≥ 0.35`: **Suspicious Flag**. Transaction held in escrow, triggering the backend integration layer.
* **n8n Outbound Automation**: Webhook fires a live alert payload to n8n, sending an instant context-aware security authorization email to the consumer.
* **Interactive User Resolution**:
  * **User Approves**: Webhook returns payload to FastAPI ➔ Status changes to *Approved* ➔ Bank releases transaction.
  * **User Rejects**: Webhook returns payload to FastAPI ➔ Status changes to *Blocked* ➔ Cards frozen, security logs generated.

---

## 🏗️ System Architecture & Data Flow

```text
[ Web Dashboard ] ──(Transaction Ingestion)──> [ FastAPI Core Engine ]
                                                         │
                                           [ ML Inference Model (0.35) ]
                                                         │
               ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
               │ Low Risk (<0.35)                                                                  │ High Risk (≥0.35)
               ▼                                                                                   ▼
        [Auto-Approved]                                                                  [Trigger n8n Webhook]
        (Bank Release)                                                                             │
               ▼                                                                                   ▼
                                                                                         [Email Alert to User]
                                                                                                   │
               ┌───────────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────┐
               │ User Approves                                                                                                                                                         │ User Rejects
               ▼                                                                                                                                                                       ▼
         [Release Ledger]                                                                                                                                                   [Block & Freeze Account]
```

---

## 🛠️ Technological Ecosystem

### 🧠 Backend & Machine Learning Stack
* **Core Language**: Python 3.11 *(Isolated using strict `.venv` environment boundaries).*
* **API Framework**: FastAPI *(Asynchronous transaction evaluation gateway).*
* **ML Science Engine**: Scikit-Learn *(Pipelines, Imbalanced Class Sampling, Random Forest/Gradient Boosting).*
* **Data Serialization**: Joblib *(Binary encapsulation of the trained classification workspace).*

### ⚙️ Automation & Storage Infrastructure
* **Workflow Engine**: n8n Integration Framework *(Self-hosted local webhook orchestration).*
* **Relational Ledger**: SQLite / PostgreSQL *(Transaction audit logs, status state-machine records).*
* **Container Environment**: Docker & Docker Compose *(Multi-stage static serving via Nginx).*

### 🎨 Frontend & Dashboard Presentation Layer
* **Core Library**: React *(Vite-powered component architecture).*
* **Styling**: Tailwind CSS *(v4 utility-first rapid utility classes).*
* **State Management**: React Hooks & Axios *(Real-time heartbeat synchronization).*

---

## 📊 Core Directory Topology

```bash
AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System/
├── backend/                # FastAPI services and endpoint drivers
│   ├── main.py             # System core router and gateway definitions
│   ├── Dockerfile          # Production-ready Python 3.11 environment runtime
│   └── schemas.py          # Strict Pydantic data validation structural rules
├── frontend/               # React UI web application
│   ├── src/                # Polling state engine and dynamic metrics view hooks
│   ├── Dockerfile          # Multi-stage container file compiling Nginx production builds
│   └── App.jsx             # Heartbeat synchronization data-layer parent container
├── data/                   # Data processing boundaries (Raw vs Processed dataset splits)
├── models/                 # Frozen predictive model binaries (.joblib format)
├── docker-compose.yml      # Multi-container multi-port cluster microservices mesh orchestrator
└── app.py                  # Live Streamlit UI demonstration presentation layer
```

---

## 📦 Production Deployment & Setup

### 📋 Prerequisites
Ensure your local host workstation contains Docker Engine and Docker Compose installed cleanly.

### 🐳 Microcontainer Orchestration (Recommended Production Setup)
To build and launch the entire application architecture locally with zero environmental overhead, execute the following commands in the root workspace directory:

```bash
# 1. Clean build all orchestration layers without image cache pollution
docker compose build --no-cache

# 2. Boot up full microservice network nodes in background detached mode
docker compose up -d

# 3. Stream real-time diagnostic output streams across the service grid
docker compose logs -f
```

Once running successfully:
* 🌐 **Frontend Live Monitoring Hub**: [http://localhost](http://localhost) *(Port 80)*
* ⚙️ **Backend Asynchronous Core API**: [http://localhost:8000](http://localhost:8000)

---

## 📄 License
This project is open-source software licensed under the **MIT License**.
