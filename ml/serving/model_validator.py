import os
import sys
import json
import logging
from datetime import datetime
import shutil
import joblib
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

# Import the email task directly to avoid circular imports or fastAPI dependency issues
from backend.app.tasks.notification_tasks import send_email_task

logger = logging.getLogger(__name__)

class ModelValidator:
    def __init__(self):
        self.history_file = os.path.join(project_root, "ml", "models", "freshness", "model_history.json")
        self.archive_dir = os.path.join(project_root, "ml", "models", "freshness", "archive")
        os.makedirs(self.archive_dir, exist_ok=True)

    def _log_history(self, record: dict):
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        history.append(record)
        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=4)

    def _cleanup_archive(self):
        """Keep only last 5 models."""
        files = [os.path.join(self.archive_dir, f) for f in os.listdir(self.archive_dir) if f.endswith(".pkl")]
        files.sort(key=os.path.getmtime)
        while len(files) > 5:
            os.remove(files[0])
            files.pop(0)

    def validate_and_promote(self, candidate_model_path: str, production_model_path: str, holdout_data_path: str) -> dict:
        import pandas as pd
        from ml.features.engineering import FeatureEngineer

        logger.info("Loading holdout data for validation...")
        try:
            df_raw = pd.read_csv(holdout_data_path)
            # Use 20% of the recent data as a dynamic holdout or just the entire provided dataset
            # (Assuming holdout_data_path contains the recent test set we want to validate on)
            fe = FeatureEngineer()
            df_transformed, feature_names = fe.transform(df_raw)
            y_test = df_raw["delivered_on_time"].values
            X_test = df_transformed[feature_names].values
        except Exception as e:
            logger.error(f"Validation failed to load data: {e}")
            return {"promoted": False, "reason": "Failed to load holdout data."}

        logger.info("Evaluating candidate model...")
        candidate_model = joblib.load(candidate_model_path)
        cand_pred = candidate_model.predict(X_test)
        cand_f1 = f1_score(y_test, cand_pred)

        logger.info("Evaluating production model...")
        prod_f1 = 0.0
        if os.path.exists(production_model_path):
            production_model = joblib.load(production_model_path)
            prod_pred = production_model.predict(X_test)
            prod_f1 = f1_score(y_test, prod_pred)
        else:
            logger.warning("No production model found. Candidate will be promoted automatically.")

        timestamp = datetime.utcnow().isoformat()
        
        # Step 3: Check condition
        if cand_f1 > (prod_f1 + 0.01):
            logger.info(f"Candidate F1 ({cand_f1:.4f}) beats Production F1 ({prod_f1:.4f}) by >1%. Promoting!")
            
            # Backup production
            if os.path.exists(production_model_path):
                backup_name = f"freshness_model_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pkl"
                backup_path = os.path.join(self.archive_dir, backup_name)
                shutil.copy2(production_model_path, backup_path)
            
            # Promote candidate
            shutil.move(candidate_model_path, production_model_path)
            
            self._cleanup_archive()
            
            record = {
                "timestamp": timestamp,
                "old_f1": prod_f1,
                "new_f1": cand_f1,
                "promoted": True,
                "reason": "Beaten required margin."
            }
            self._log_history(record)
            
            # Send Email
            email_body = f"Model Retrained and Promoted.\nOld F1: {prod_f1:.4f}\nNew F1: {cand_f1:.4f}"
            send_email_task.delay("admin@foodbridge.ai", "ML Model Promoted to Production", email_body)
            
            return record
        else:
            logger.info(f"Candidate F1 ({cand_f1:.4f}) did not beat Production F1 ({prod_f1:.4f}) by 1%. Discarding.")
            if os.path.exists(candidate_model_path):
                os.remove(candidate_model_path)
                
            record = {
                "timestamp": timestamp,
                "old_f1": prod_f1,
                "new_f1": cand_f1,
                "promoted": False,
                "reason": "Did not beat production by required margin."
            }
            self._log_history(record)
            
            email_body = f"Model Retraining completed but NOT promoted.\nProduction F1: {prod_f1:.4f}\nCandidate F1: {cand_f1:.4f}"
            send_email_task.delay("admin@foodbridge.ai", "ML Model Retrain: No Promotion", email_body)
            
            return record
