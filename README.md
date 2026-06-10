# AI-Empowered Fintech Fraud Detection and Control Automation System

[![Python 3.11](https://shields.io)](https://python.org)
[![FastAPI](https://shields.io)](https://tiangolo.com)
[![Automation](https://shields.io)](https://n8n.io)
[![License: MIT](https://shields.io)](https://opensource.org)

An enterprise-grade, real-time automated fraud detection and risk mitigation engine designed for modern financial technology and core banking layers.

---

## 🎓 Final Year Project / Portfolio Presentation
- **Author:** Mohammad Usman
- **University:** Minhaj University Lahore
- **Supervisor:** Dr. Gulzar Ahmad
- **Academic Year:** 2026

---

## 🎯 Project Overview & Vision
Modern financial transaction systems process millions of orders per second. Standard static rules fail against evolving fraud patterns. This system bridges the gap by injecting an **intelligent machine learning inference layer (FastAPI)** between transaction ingestion and bank processing, coupled with an **automated incident management pipeline (n8n)**.

### 🔄 Core Automation Control Loop:
1. **Ingestion & Ingestion:** Transactions are initiated via the real-time financial web dashboard.
2. **AI Scoring Model:** A predictive machine learning pipeline calculates an explicit fraud probability score.
3. **Threshold-based Triage:** 
   * **Score < 0.35:** Approved immediately. Bank core system executes the ledger release.
   * **Score ≥ 0.35:** Suspicious flag. Transaction held in escrow, triggering the backend integration layer.
4. **n8n Outbound Automation:** Webhook fires a live alert payload to n8n, sending an instant context-aware security authorization email to the consumer.
5. **Interactive User Resolution:**
   * **If User Approves:** Webhook returns payload to FastAPI -> Status changes to `Approved` -> Bank releases transaction.
   * **If User Rejects:** Webhook returns payload to FastAPI -> Status changes to `Blocked` -> Cards frozen, security logs generated.

---

## 🏗️ System Architecture & Data Flow

```text
[Web Dashboard Dashboard] ---> (Transaction Ingestion) ---> [FastAPI Core Engine]
                                                                  |
                                                     [ML Inference Model (0.35)]
                                                                  |
                                                    +-------------+-------------+

                                                    | Low Risk                  | High Risk (≥0.35)
                                                    v                           v
                                            [Auto-Approved]             [Trigger n8n Webhook]
                                            (Bank Release)                      |
                                                                                v
                                                                     [Email Dispatch to User]
                                                                                |
                                                                     +----------+----------+

                                                                     |                     |
                                                                     v User Approves       v User Rejects
                                                               [Release Ledger]     [Block & Freeze Account]
```

---

## 🛠️ Technological Ecosystem

### Backend & Machine Learning Stack
* **Core Language:** Python 3.11 (Isolated using `.venv`)
* **API Framework:** FastAPI (Asynchronous transaction evaluation gateway)
* **ML Science Engine:** Scikit-Learn (Pipelines, Imbalanced Class Sampling, Random Forest/Gradient Boosting)
* **Data Serialization:** Joblib (Binary encapsulation of the trained classification workspace)

### Automation & Storage Infrastructure
* **Workflow Engine:** n8n Integration Framework (Self-hosted / Local Webhook orchestration)
* **Relational Ledger:** SQLite / PostgreSQL (Transaction audit logs, status state-machine records)
* **Container Environment:** Docker & Docker Compose (System stack replication and deployment)

---

## 📊 Core Directory Topology

```text
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
└── app.py                  # Live UI demonstration presentation layer
```

---

## 🚀 Installation & Local Workspace Activation

### Prerequisites
Ensure your operating system contains **Python 3.11** and **Git**.

### 1. Repository Instantiation & Alignment
```bash
git clone https://github.com
cd AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System
```

### 2. Environment Insulation & Packages Ingestion
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
Your secure banking control application will automatically resolve onto your visual thread loop at `http://localhost:8501`.

---

## 📄 License
This project is open-source software licensed under the [MIT License](LICENSE).
