# Fraud Detection Platform (Portfolio Project)

End-to-end data project demonstrating:
- SQL data modeling and analytics
- Data science workflow for fraud detection
- API deployment pattern for real-time risk scoring

## Tech Stack
- PostgreSQL
- Python (`pandas`, `scikit-learn`, `xgboost`, `sqlalchemy`)
- FastAPI
- Docker Compose

## Project Structure
- `sql/` database schema + analysis queries
- `src/data/` synthetic data generation
- `src/features/` feature engineering
- `src/models/` training and evaluation
- `src/api/` fraud scoring API
- `data/` local datasets
- `models/` trained model artifacts

## Quick Start
1. Create a virtual environment and install dependencies:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r requirements.txt`
2. Start PostgreSQL:
   - `docker compose up -d`
3. Generate synthetic transactions:
   - `python -m src.data.generate_synthetic_data`
4. Load data into PostgreSQL:
   - `set DATABASE_URL=postgresql+psycopg2://fraud_user:fraud_pass@localhost:5432/fraud_db`
   - `python -m src.data.load_to_postgres`
5. Train baseline model:
   - `python -m src.models.train_model`
6. Run API:
   - `uvicorn src.api.main:app --reload`
7. Open dashboard:
   - `http://127.0.0.1:8000/`
   - Use tabs for Transaction, Website URL, and File checks

## Deploy (Render)
1. Push this project to GitHub.
2. In Render, choose **New +** -> **Blueprint**.
3. Select your repo (Render reads `render.yaml`).
4. Deploy; Render builds from `Dockerfile` and starts `uvicorn` on port `8000`.

Alternative manual deploy (Render Web Service):
- Environment: `Docker`
- Start command: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- Port: `8000`

## Deploy (Vercel)
1. Push this project to GitHub.
2. Import the repo into Vercel.
3. Vercel uses `vercel.json` and deploys `api/index.py`.
4. Build command: leave empty (default).
5. Output: not required for Python runtime.

CLI deploy option:
- `npm i -g vercel` (once)
- `vercel` (first deploy, follow prompts)
- `vercel --prod` (production deploy)

## API Example
- Endpoint: `POST /score`
- Sample body:
```json
{
  "amount": 245.5,
  "channel": "web",
  "card_present": 0,
  "hour": 2
}
```

## Additional Endpoints
- `GET /` interactive fraud dashboard UI
- `GET /metrics` model metrics for dashboard cards
- `POST /score/batch` batch scoring for up to 200 transactions
- `POST /check/url` heuristic phishing-style URL risk check
- `POST /check/file` heuristic file risk check via multipart upload

## Notes
- URL and file checks are heuristic signals for portfolio demonstration and analyst triage workflows.
- They do not replace production threat-intel engines or malware sandboxes.

## CV Highlights You Can Claim
- Designed normalized fraud data model in PostgreSQL with indexed transactional queries
- Built and evaluated machine learning fraud model with ROC-AUC and precision-recall metrics
- Exposed real-time fraud risk scoring via FastAPI service
- Implemented reproducible local environment with Docker Compose

## Suggested Next Steps
- Replace synthetic data with a public fraud dataset (Kaggle/IEEE-CIS style)
- Add dbt models for warehouse layers
- Add scheduler (Airflow/Prefect) and CI pipeline
- Add dashboard (Power BI/Tableau)
