# FinGuard MLOps Guide

This document outlines how to manage the AI Fraud Detection model lifecycle using MLflow and DVC.

## 1. Running MLflow Tracking Server

The MLflow tracking server is containerized and managed via Docker Compose.
Start it along with the rest of the services:

```bash
docker-compose up -d mlflow
```

The server is available at `http://localhost:5000`.

## 2. Training with MLflow Tracking

The training and evaluation scripts have been integrated with MLflow. All parameters, metrics, and models are automatically logged to the tracking server.

To run the pipeline and log to MLflow:
```bash
# Ensure MLFLOW_TRACKING_URI is set (e.g. from .env)
export MLFLOW_TRACKING_URI=http://localhost:5000
python src/train_model.py
python src/evaluate.py
```

## 3. Working with the Model Registry

The backend application (`backend/services/ml_service.py`) automatically attempts to fetch the latest model from the MLflow Model Registry tagged with the `Production` stage. If it fails, it falls back to the local `models/fraud_pipeline.joblib`.

### Promoting a Model to Production
We provide an interactive script to promote the best runs:

```bash
python src/promote_model.py
```
This script will:
1. List the most recent training runs.
2. Let you choose a run by index.
3. Register the chosen run's model as `finguard_fraud_model`.
4. Transition its stage to `Production` (and archive the previous production model).

Restart the backend container to load the newly promoted model.

## 4. DVC (Data Version Control)

DVC is used to track changes to our raw and processed datasets so they do not bloat the git repository.

### Initial Setup (Already Run in Phase 4)
```bash
dvc init
dvc remote add -d storage /dvc_storage
dvc add data/raw/synthetic_fraud_dataset.csv
dvc add data/processed/transactions_train.csv
dvc add data/processed/transactions_test.csv
git add .dvc .gitignore data/**/*.dvc
```

### Running the DVC Pipeline
The entire ML workflow (data preparation, training, evaluation, threshold policy) is codified in `dvc.yaml`.

To execute the pipeline end-to-end:
```bash
dvc repro
```
This will run the necessary stages if their dependencies have changed.

### Fetching Data on a New Machine
To pull tracked data from external storage:
```bash
dvc pull
```
