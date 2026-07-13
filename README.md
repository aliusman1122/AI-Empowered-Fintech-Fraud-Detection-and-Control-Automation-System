---
# 🛡️ FinGuard: AI-Empowered Fintech Fraud Detection & Control Automation System

An enterprise-grade, real-time automated fraud detection and risk mitigation engine designed for modern financial technology and core banking layers.

🎓 **Final Year Project / Portfolio Presentation**
* **Author:** Mohammad Usman
* **University:** Minhaj University Lahore
* **Supervisor:** Dr. Gulzar Ahmad
* **Academic Year:** 2026

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
┌───────────────────────────┴───────────────────────────┐
│ Low Risk (<0.35)                                      │ High Risk (≥0.35)
▼                                                       ▼
[Auto-Approved]                                      [Trigger n8n Webhook]
(Bank Release)                                                 │
▼
[Email Alert to User]
│
┌────────────────────────┴────────────────────────┐
│ User Approves                                   │ User Rejects
▼                                                 ▼
[Release Ledger]                               [Block & Freeze Account]
```

---

## 🛠️ Technological Ecosystem

### 🧠 Backend & Machine Learning Stack
* **Core Language**: Python 3.11 (Isolated using strict `.venv` environment boundaries).
* **API Framework**: FastAPI (Asynchronous transaction evaluation gateway).
* **ML Science Engine**: Scikit-Learn (Pipelines, Imbalanced Class Sampling, Random Forest/Gradient Boosting).
* **Data Serialization**: Joblib (Binary encapsulation of the trained classification workspace).

### ⚙️ Automation & Storage Infrastructure
* **Workflow Engine**: n8n Integration Framework (Self-hosted local webhook orchestration).
* **Relational Ledger**: SQLite / PostgreSQL (Transaction audit logs, status state-machine records).
* **Container Environment**: Docker & Docker Compose (System stack replication and deployment).

---

## 📊 Core Directory Topology

```bash
AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System/
├── .github/workflows/      # Automated CI production test files
├── backend/                # FastAPI services and endpoint drivers (Phase 4)
│   ├── main.py             # System core router and gateway definitions
│   ├── database.py         # Relational database connector layers
│   ├── models.py           # Table schematics (transactions, verification logs)
│   └── schemas.py          # Strict Pydantic data validation structural rules
├── data/                   # Data processing boundaries
│   ├── raw/                # Synthetic financial base csv distributions
│   └── processed/          # Training/Testing class stratified dataset splits
├── models/                 # Frozen predictive model binaries (.joblib)
├── reports/                # AI analytical artifacts, plots, and json matrix summaries
├── src/                    # Data preparation and ML model execution runtimes
└── app.py                  # Live Streamlit UI demonstration presentation layer
```

---

## 📦 Setup & Workspace Activation

### 📋 Prerequisites
Ensure your operating system contains Python 3.11 and Git configured locally.

### 1. Installation & Cloning
```bash
git clone https://github.com/aliusman1122/AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System.git
cd AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System
```

### 2. Environment Insulation & Dependencies
```bash
# Windows specific architecture launcher
py -3.11 -m venv .venv
.venv\Scripts\activate

# Dependency compilation
pip install -r requirements.txt
```

### 3. Execution Sequence & Model Pipeline Generation
```bash
# Ingest baseline evaluation raw files
python -m src.generate_synthetic_data --rows 3500 --fraud-rate 0.08 --label-noise 0.04 --seed 42 --output data/raw/synthetic_fraud_dataset.csv

# Execute data cleanup and split pipelines
python -m src.data_prep

# Ingest training constraints and output trained model
python -m src.train_model

# Run comprehensive metric evaluations
python -m src.evaluate
```

### 4. Interactive Live System Launch
```bash
streamlit run app.py
```
Your secure banking control application will automatically resolve onto your visual thread loop at http://localhost:8501.

---

## 📄 License
This project is open-source software licensed under the MIT License.
