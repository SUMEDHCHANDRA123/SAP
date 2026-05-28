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

| Guide | Stack |
|-------|--------|
| **[DEPLOYMENT_NETLIFY.md](DEPLOYMENT_NETLIFY.md)** | Frontend on **Netlify** + API on **Render** |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Everything on **Render** (Blueprint) |

Netlify quick path:
1. Deploy API with Render Blueprint (`render.yaml`) — API, worker, Postgres, Redis
2. Netlify → import GitHub repo (`netlify.toml` configures the build)
3. Set `VITE_API_URL` to your Render API URL; add Netlify URL to Render `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS`
4. Login with `admin` / `admin123` (after `RUN_SEED=true` on first API deploy)
# SAP
