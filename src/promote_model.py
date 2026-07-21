import os
import sys
import mlflow
from mlflow.tracking import MlflowClient

def main():
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(mlflow_uri)
    client = MlflowClient()
    
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "finguard_fraud_detection")
    experiment = client.get_experiment_by_name(experiment_name)
    if not experiment:
        print(f"Experiment '{experiment_name}' not found. Ensure you have run training first.")
        sys.exit(1)
        
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attribute.start_time DESC"],
        max_results=10
    )
    
    if not runs:
        print("No runs found in the experiment.")
        sys.exit(0)
        
    print("\n=== Recent MLflow Runs ===")
    for idx, run in enumerate(runs):
        metrics = run.data.metrics
        roc_auc = metrics.get("roc_auc", "N/A")
        if isinstance(roc_auc, float):
            roc_auc = round(roc_auc, 4)
        run_name = run.data.tags.get("mlflow.runName", "unnamed")
        print(f"[{idx}] ID: {run.info.run_id} | Name: {run_name} | ROC-AUC: {roc_auc}")
        
    try:
        choice = input("\nEnter index of the run to promote to Production (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            print("Exiting.")
            sys.exit(0)
        choice_idx = int(choice)
        if choice_idx < 0 or choice_idx >= len(runs):
            print("Invalid index.")
            sys.exit(1)
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\nExiting.")
        sys.exit(0)
        
    selected_run = runs[choice_idx]
    run_id = selected_run.info.run_id
    model_name = "finguard_fraud_model"
    
    print(f"\nRegistering Run {run_id} to Model Registry as '{model_name}'...")
    try:
        model_uri = f"runs:/{run_id}/model"
        mv = mlflow.register_model(model_uri, model_name)
        print(f"Version {mv.version} registered successfully.")
        
        print("Transitioning to 'Production' stage (archiving existing)...")
        client.transition_model_version_stage(
            name=model_name,
            version=mv.version,
            stage="Production",
            archive_existing_versions=True
        )
        print("✅ Successfully promoted! The backend will load this model upon restart.")
    except Exception as e:
        print(f"Failed to promote model: {e}")

if __name__ == "__main__":
    main()
