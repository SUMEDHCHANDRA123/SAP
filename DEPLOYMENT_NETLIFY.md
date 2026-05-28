# Deploy Breathe ESG (Netlify + Render)

Netlify hosts the **React dashboard** only. The **Django API**, PostgreSQL, Redis, and Celery worker run on [Render](https://render.com) (free tier).

| Part | Platform |
|------|----------|
| Frontend (React) | **Netlify** |
| API + DB + Worker | **Render** (`render.yaml`, skip the static frontend service if you use Netlify) |

## Prerequisites

1. Code on GitHub
2. [Netlify](https://app.netlify.com/) account
3. [Render](https://render.com) account (for backend)

---

## Part A — Backend on Render

1. [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
2. Connect your GitHub repo
3. Apply `render.yaml`

   **Optional:** If you only want Netlify for the UI, delete or disable the `breathe-esg-frontend` static service in the Blueprint before deploy (API, worker, Postgres, Redis stay).

4. When the API is live, copy its URL, e.g. `https://breathe-esg-api.onrender.com`

5. On **breathe-esg-api** → **Environment**, set (replace with your real Netlify URL after Part B):

   | Variable | Example |
   |----------|---------|
   | `CORS_ALLOWED_ORIGINS` | `https://your-app.netlify.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://your-app.netlify.app` |
   | `CROSS_SITE_COOKIES` | `true` |
   | `DJANGO_DEBUG` | `false` |
   | `RUN_SEED` | `true` (first deploy only, then `false`) |

   If you use a custom domain on Netlify, include both URLs comma-separated.

6. **Redeploy** the API after updating CORS/CSRF.

Default seed login (when `RUN_SEED=true`):

- Username: `admin`
- Password: `admin123`

---

## Part B — Frontend on Netlify

### Option 1 — GitHub (recommended)

1. [Netlify](https://app.netlify.com/) → **Add new site** → **Import an existing project**
2. Connect GitHub and select your repo
3. Netlify reads `netlify.toml` at the repo root (base dir `breathe_esg_frontend`, publish `dist`)
4. **Site configuration** → **Environment variables** → add:

   | Key | Value |
   |-----|--------|
   | `VITE_API_URL` | `https://breathe-esg-api.onrender.com` (your Render API URL, no trailing slash) |

5. **Deploy site**

6. Copy your Netlify URL (e.g. `https://breathe-esg.netlify.app`) and add it to Render `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`, then redeploy the API.

### Option 2 — Netlify CLI

```bash
npm install -g netlify-cli
netlify login
cd "d:\Sumedh\Breathe ESG"
netlify init
netlify env:set VITE_API_URL "https://breathe-esg-api.onrender.com"
netlify deploy --prod
```

---

## Verify

1. Open your Netlify URL → **Login**
2. API docs: `https://<your-api>.onrender.com/api/docs/`
3. Upload a CSV on **Upload** and check **Jobs**

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Login / CSRF errors | Set `VITE_API_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `CROSS_SITE_COOKIES=true`; redeploy API and Netlify |
| Blank page on `/analytics` | `netlify.toml` SPA redirect is included; trigger a new deploy |
| API 502 on Render free tier | Wake the service (first request after idle can take ~1 min) |
| CORS blocked | Netlify URL must exactly match env vars (https, no trailing slash) |

---

## Why not all-in-one on Netlify?

Netlify serves static sites and serverless functions. This project needs a long-running Django app, PostgreSQL, and Celery — use Render (or Railway/Fly.io) for the API.
