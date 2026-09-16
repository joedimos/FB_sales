# FB Sales — Marketplace Lead Prioritization

A dealership sales workspace that ranks Facebook Marketplace leads by predicted transaction likelihood. The repository contains ingestion, storage, model-training and CRM writeback components plus a responsive web dashboard.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

On first run the app creates the SQLite schema and, only when the database has no leads, adds four demo leads so the interface is immediately usable. Real ingested data is never replaced by the demo seed.

## Dashboard

The web UI provides:

- an at-a-glance pipeline summary;
- a likelihood-ranked lead inbox;
- search across lead IDs, vehicles and messages;
- status filtering;
- responsive layouts for desktop, tablet and phone;
- keyboard-visible focus, semantic table markup, a skip link, readable contrast and reduced-motion support.

## Configuration

`config/settings.yaml` contains the default local configuration. The default database is `sqlite:///fb_sales.db`. `DATABASE_URL` and `MODEL_PATH` environment variables can override the corresponding settings.

CRM writeback is disabled in the sample configuration. Do not commit production credentials.

## Tests

```bash
pytest -q
```

The smoke tests cover the dashboard, health endpoint, lead API and summary API.

## Existing ML pipeline

The original ingestion, feature engineering, training and CRM writeback modules remain under `src/`. The dashboard intentionally works even before a trained model is available: unscored leads are shown as `Not scored` instead of preventing the sales workspace from starting.

The legacy prediction service still needs deeper consolidation before production use; the original source contains stale `prediction_service` / `feature_engineering` import paths and assumptions around model loading. The dashboard is the stable runnable entry point while that API is modernized.

## Production notes

For deployment, run the Flask app behind a production WSGI server and reverse proxy, disable demo seeding if your deployment process preloads data, use a managed database, configure authentication/authorization, and store CRM credentials in a secret manager.
