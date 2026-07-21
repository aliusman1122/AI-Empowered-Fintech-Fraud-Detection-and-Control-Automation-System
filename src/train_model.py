from __future__ import annotations

import json

import joblib
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    roc_auc_score,
)

import mlflow
import mlflow.sklearn
import os

from .config import METRICS_DIR, MODELS_DIR, PROCESSED_DATA_DIR, TARGET_COL
from .features import build_pipeline
from .validation import validate_training_dataframe


def load_processed_data():
    train_path = PROCESSED_DATA_DIR / "transactions_train.csv"
    test_path = PROCESSED_DATA_DIR / "transactions_test.csv"

    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            f"Processed train/test files not found in {PROCESSED_DATA_DIR}. "
            f"Run data_prep.py first."
        )

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    validate_training_dataframe(train_df, context="processed training data")
    validate_training_dataframe(test_df, context="processed test data")
    return train_df, test_df


def train_and_evaluate() -> dict:
    train_df, test_df = load_processed_data()

    X_train = train_df.drop(columns=[TARGET_COL])
    y_train = train_df[TARGET_COL]

    X_test = test_df.drop(columns=[TARGET_COL])
    y_test = test_df[TARGET_COL]

    # Setup MLflow
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow_exp = os.getenv("MLFLOW_EXPERIMENT_NAME", "finguard_fraud_detection")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(mlflow_exp)

    with mlflow.start_run(run_name="train_model"):
        # We can extract basic params from the pipeline if needed
        # but for simplicity we log a few high level concepts
        mlflow.log_param("model_type", "RandomForestClassifier")
        
        pipeline = build_pipeline()
        pipeline.fit(X_train, y_train)

        y_proba = pipeline.predict_proba(X_test)[:, 1]
        y_pred_default = (y_proba >= 0.5).astype(int)

        roc_auc = roc_auc_score(y_test, y_proba)
        average_precision = average_precision_score(y_test, y_proba)
        brier_score = brier_score_loss(y_test, y_proba)

        cls_report = classification_report(
            y_test,
            y_pred_default,
            output_dict=True,
            digits=3,
        )

        metrics = {
            "roc_auc": float(roc_auc),
            "average_precision": float(average_precision),
            "brier_score": float(brier_score),
            "n_train_samples": int(len(y_train)),
            "n_test_samples": int(len(y_test)),
            "positive_rate_train": float(y_train.mean()),
            "positive_rate_test": float(y_test.mean()),
        }

        # Log metrics to MLflow
        mlflow.log_metrics({
            "roc_auc": float(roc_auc),
            "pr_auc": float(average_precision),
            "brier_score": float(brier_score),
            "accuracy": cls_report["accuracy"],
            "precision": cls_report["macro avg"]["precision"],
            "recall": cls_report["macro avg"]["recall"],
            "f1_score": cls_report["macro avg"]["f1-score"],
        })

        model_path = MODELS_DIR / "fraud_pipeline.joblib"
        joblib.dump(pipeline, model_path)

        metrics_path = METRICS_DIR / "metrics.json"
        with metrics_path.open("w") as f:
            json.dump(metrics, f, indent=2)

        # Log artifacts and model
        try:
            mlflow.log_artifact(str(metrics_path), artifact_path="reports")
            mlflow.sklearn.log_model(pipeline, "model")
        except Exception as e:
            print(f"Warning: Failed to log to MLflow: {e}")

        print(f"Saved model to:   {model_path}")
        print(f"Saved metrics to: {metrics_path}")
        print(f"ROC-AUC (test): {roc_auc:.4f}")
        print(f"Average precision (test): {average_precision:.4f}")
        print(f"Brier score (test): {brier_score:.4f}")

    return metrics


def main() -> None:
    metrics = train_and_evaluate()
    print("\n=== Metrics summary ===")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
