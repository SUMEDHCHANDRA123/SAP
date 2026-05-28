# Breathe ESG

Production-oriented carbon emissions ingestion and governance platform.

## Key Capabilities

- Multi-source ingestion (SAP, utility, travel)
- Async ingestion jobs with Celery-ready task pipeline
- Data quality scoring and issue snapshots
- Emission factor catalog with versioned CO2e calculation trace
- Staged approval workflow and immutable audit events
- Analytics APIs (summary, breakdown, trends, anomalies, targets, benchmarks, scenarios)
- Frontend dashboard for upload/review/history/analytics

## Local Run

```bash
pip install -r requirements.txt
python manage.py migrate
python seed.py
python manage.py runserver
```

Frontend:

```bash
cd breathe_esg_frontend
npm install --legacy-peer-deps
npm run dev
```

## API Docs

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Production Notes

- Set PostgreSQL vars (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`)
- Set Redis/Celery vars (`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`)
- Set `CELERY_TASK_ALWAYS_EAGER=false` for worker-based execution

## Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for full Render deployment steps (Blueprint + env vars + login).

Quick path:
1. Push repo to GitHub
2. Render → **New Blueprint** → select repo (`render.yaml` included)
3. Open frontend URL and login with `admin` / `admin123` (after seed runs)
