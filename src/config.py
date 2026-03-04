from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

RAW_TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"
MODEL_PATH = MODELS_DIR / "fraud_xgb.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"
