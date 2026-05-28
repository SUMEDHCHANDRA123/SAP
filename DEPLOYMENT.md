# Deploy Breathe ESG (Render)

This guide deploys:
- **API** (`breathe-esg-api`) – Django + Gunicorn
- **Worker** (`breathe-esg-worker`) – Celery
- **Frontend** (`breathe-esg-frontend`) – React static site
- **PostgreSQL** + **Redis**

## Prerequisites

1. GitHub account
2. [Render](https://render.com) account (free tier works for demo)
3. Project pushed to a GitHub repository

## Step 1 — Push code to GitHub

```bash
git init
git add .
git commit -m "Prepare Breathe ESG for deployment"
git branch -M main
git remote add origin https://github.com/<your-user>/<your-repo>.git
git push -u origin main
```

Do **not** commit `.env`, `db.sqlite3`, or `node_modules`.

## Step 2 — Deploy with Render Blueprint

1. Open [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates all services
5. Click **Apply**

First deploy takes ~10–15 minutes (free tier services spin up slowly).

## Step 3 — Get your live URLs

After deploy succeeds:

| Service | URL example |
|---------|-------------|
| Frontend | `https://breathe-esg-frontend.onrender.com` |
| API | `https://breathe-esg-api.onrender.com` |
| API docs | `https://breathe-esg-api.onrender.com/api/docs/` |

## Step 4 — Verify environment variables

On **breathe-esg-api** → **Environment**, confirm:

| Variable | Value |
|----------|--------|
| `DJANGO_DEBUG` | `false` |
| `DATABASE_URL` | (auto from Postgres) |
| `CELERY_BROKER_URL` | (auto from Redis) |
| `CELERY_TASK_ALWAYS_EAGER` | `false` |
| `CROSS_SITE_COOKIES` | `true` |
| `CORS_ALLOWED_ORIGINS` | frontend URL |
| `CSRF_TRUSTED_ORIGINS` | frontend URL |
| `RUN_SEED` | `true` (first deploy only, then set `false`) |

On **breathe-esg-frontend** → **Environment**:

| Variable | Value |
|----------|--------|
| `VITE_API_URL` | `https://breathe-esg-api.onrender.com` |

If login fails with CSRF errors, redeploy **frontend** after API URL is final.

## Step 5 — Login credentials

Default seeded admin (created when `RUN_SEED=true`):

- **Username:** `admin`
- **Password:** `admin123`

Change admin password after first login:

```bash
# Render API shell, or locally with production DATABASE_URL
python manage.py changepassword admin
```

## Step 6 — Test the deployed app

1. Open frontend URL
2. Login as `admin` / `admin123`
3. Select tenant **Demo Corp**
4. Upload a CSV on **Upload**
5. Review records on **Review**
6. Check **Analytics**

## Troubleshooting

### “CSRF token missing”
- Ensure `CROSS_SITE_COOKIES=true` on API
- Ensure `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` match frontend URL exactly (https, no trailing slash)
- Redeploy frontend after setting `VITE_API_URL`

### API 502 / slow first request
- Free tier sleeps after inactivity; first request may take 30–60s

### Upload stuck on “Processing”
- Check **breathe-esg-worker** logs on Render
- Confirm Redis is connected (`CELERY_BROKER_URL`)

### Media/uploads lost after restart
- Render free disk is ephemeral; for production use S3-compatible storage (not included in this prototype)

## Optional: Manual deploy (without Blueprint)

Create services manually on Render:

1. **PostgreSQL** database → copy `DATABASE_URL`
2. **Redis** → copy connection string
3. **Web Service** (Python):
   - Build: `./scripts/render_build.sh`
   - Start: `./scripts/render_start.sh`
4. **Background Worker** (Python):
   - Start: `./scripts/celery_worker.sh`
5. **Static Site**:
   - Root: `breathe_esg_frontend`
   - Build: `npm install --legacy-peer-deps && npm run build`
   - Publish: `dist`

## Submission checklist

- [ ] Live frontend URL works
- [ ] Live API URL works (`/api/docs/`)
- [ ] Login works
- [ ] Upload + review flow works
- [ ] GitHub repo link shared with reviewers
- [ ] Credentials included in submission email
