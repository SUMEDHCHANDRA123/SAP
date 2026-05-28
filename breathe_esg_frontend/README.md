# Breathe ESG Frontend

React dashboard for carbon emissions data ingestion and review.

## Setup

```bash
cd breathe_esg_frontend
npm install --legacy-peer-deps
cp .env.example .env   # or use existing .env
npm run dev
```

Open http://localhost:5173

Ensure the Django backend is running at http://localhost:8000

Sample CSV files are in `../sample_data/` at the project root.

## Pages

- `/upload` — Upload SAP, Utility, or Travel CSV files
- `/records` — Review and approve/flag/reject emission records
- `/jobs` — Ingestion history (click row to filter records by job)
