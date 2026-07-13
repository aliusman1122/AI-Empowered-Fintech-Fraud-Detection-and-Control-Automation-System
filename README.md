---
# FinGuard: AI-Empowered Fintech Fraud Detection & Control Automation System

FinGuard is a production-grade, high-performance financial risk mitigation platform designed to intercept fraudulent transactions in real time. Combining an asynchronous FastAPI backend engine, an adaptive React dashboard featuring live telemetry synchronization, and an automated n8n orchestration workflow, the system achieves instant "Hold-First" validation and human-in-the-loop closure before financial leakage occurs.

## 🏗️ System Architecture & Telemetry Flow

The ecosystem functions via a three-way state synchronization architecture:
1. **Ingestion & AI Scoring**: Transactions are intercepted via webhooks and processed by a Python inference node using strict Pydantic model validation. Transactions exceeding the 35% risk threshold are marked for intervention.
2. **Orchestration Network (n8n)**: High-risk events trigger automated webhooks that put funds on conditional hold and fire asynchronous email alerts containing interactive callback tokens.
3. **Reactive Frontend Monitoring**: The React dashboard executes a continuous 4-second background heartbeat synchronization (polling loop). It leverages defensive rendering and native filtering layers to compute real-time metrics even during aggregate API micro-outages.

[ Financial Ingestion UI ] ──(Webhook)──> [ FastAPI Inference Engine ]
│ (Risk > 35%)
▼
[ React Dashboard (4s Poll) ] <──(Sync)─── [ n8n Orchestrator ]
▲                                           │
└───────────(Callback Actions)──────────────┴──> [ Step-Up Email Auth ]

## 🛠️ Technical Stack & Frameworks
* **Backend Core**: FastAPI (Python), Pydantic v2 validation, Uvicorn asynchronous server.
* **Frontend Center**: React.js (Vite), Recharts Engine, Axios Client, Tailwind CSS architecture.
* **Workflow Automation**: n8n Workflow Automation Server, Interactive Webhook Nodes.

## 🚀 Key Features & Defensive Engineering
* **Zero-Crash Stability Layer**: Implemented rigorous null-safety and runtime try/catch blocks across the UI aggregation stream to process dynamic payloads without rendering drops.
* **Dynamic Metrics Processing**: Real-time evaluation of `Fraud Alerts`, `Auto-Approved`, and `Pending Verifications` natively computed straight from the polled state data stream.
* **Bi-directional Webhook Sync**: End-to-end atomic workflow mapping state shifts (`BLOCKED`, `APPROVED`, `VERIFICATION_SENT`) instantaneously across database segments and user client apps.

## 📦 Setup & Deployment Guide

### Prerequisites
* Python 3.10+
* Node.js 18+
* n8n instance setup

### 1. Backend Installation
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend Installation
```bash
cd frontend
npm install
npm run dev
```
