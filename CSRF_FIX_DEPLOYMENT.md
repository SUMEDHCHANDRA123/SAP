# CSRF Token Fix - Deployment Guide

## Problem
When deploying Django (Render) + React (Netlify), you encounter "CSRF token missing" error during login.

## Root Cause
1. Django's CSRF protection requires the frontend to send a valid CSRF token with POST/DELETE/PATCH requests.
2. In production with cross-origin setup (frontend on Netlify, backend on Render), the CSRF cookie may not be set before login.
3. The previous implementation used `@csrf_exempt` decorator which disabled CSRF protection entirely (security risk).

## Solution Applied

### Backend Changes (Django)
1. **Removed `@csrf_exempt` decorator** from authentication endpoints (`AuthMeView.post`, `AuthMeView.delete`, `AuthRegisterView.post`).
2. **Kept `@ensure_csrf_cookie`** on `AuthMeView.get` to set the CSRF cookie when fetching user info.

### Frontend Changes (React)
1. **Added `fetchCsrfToken()`** function to pre-fetch CSRF token from backend before login/registration.
2. **Updated `loginSession()`** to fetch CSRF token before making the login POST request.
3. **Updated `registerUser()`** to fetch CSRF token before registration.
4. **Added CSRF token caching** in localStorage to avoid repeated fetches.

## Environment Variables Configuration

### On Render (Backend Service)

Set these environment variables in your Render dashboard:

```bash
# Core Django Settings
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<your-secret-key>  # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Database (auto-configured by Render)
DATABASE_URL=<auto-from-render-postgres>

# CORS & CSRF
CORS_ALLOWED_ORIGINS=https://your-app-name.netlify.app
CSRF_TRUSTED_ORIGINS=https://your-app-name.netlify.app

# Cross-site cookie settings (CRITICAL for Netlify + Render)
CROSS_SITE_COOKIES=true

# Celery & Redis
CELERY_BROKER_URL=<auto-from-render-redis>
CELERY_RESULT_BACKEND=<auto-from-render-redis>
CELERY_TASK_ALWAYS_EAGER=false

# First deploy only
RUN_SEED=true  # Set to false after first deploy
```

### On Netlify (Frontend)

Set these environment variables in your Netlify dashboard (Site settings > Environment variables):

```bash
VITE_API_URL=https://your-backend-app.onrender.com
```

**Important**: Do NOT include trailing slash in `VITE_API_URL`.

## Step-by-Step Deployment

### 1. Deploy Backend on Render

1. Go to Render Dashboard
2. Create a new Blueprint using `render.yaml`
3. Set all required environment variables (see above)
4. Deploy the backend service
5. Note your backend URL: `https://your-backend-app.onrender.com`

### 2. Deploy Frontend on Netlify

1. Connect your GitHub repository to Netlify
2. Set build settings (already configured in `netlify.toml`):
   - Build command: `npm install --legacy-peer-deps && npm run build`
   - Publish directory: `dist`
3. Set environment variable:
   - `VITE_API_URL=https://your-backend-app.onrender.com`
4. Deploy

### 3. Update CORS/CSRF Settings on Render

After Netlify deployment completes:

1. Copy your Netlify URL (e.g., `https://breathe-esg.netlify.app`)
2. Go to Render Dashboard > your API service > Environment
3. Update these variables:
   ```
   CORS_ALLOWED_ORIGINS=https://breathe-esg.netlify.app
   CSRF_TRUSTED_ORIGINS=https://breathe-esg.netlify.app
   ```
4. Redeploy the backend service

### 4. Test Login

1. Open your Netlify frontend URL
2. Clear browser cookies/cache for both domains
3. Try to login with `admin` / `admin123`
4. Should work without CSRF errors

## How It Works

### Login Flow
1. User visits Netlify frontend
2. Frontend calls `fetchCsrfToken()` → GET request to `https://backend.onrender.com/api/auth/me/`
3. Django responds with:
   - Sets CSRF cookie in browser (via `@ensure_csrf_cookie`)
   - Frontend extracts token from cookie and caches in localStorage
4. User submits login form
5. Frontend makes POST request to `/api/auth/me/` with:
   - CSRF token in `X-CSRFToken` header
   - `withCredentials: true` (sends cookies)
6. Django validates CSRF token and authenticates user
7. Session cookie is set for subsequent requests

### Subsequent Requests
1. Frontend reads CSRF token from localStorage (or cookie)
2. Includes token in `X-CSRFToken` header for all POST/PATCH/DELETE requests
3. Django validates token and processes request

## Troubleshooting

### "CSRF token missing" error
**Solutions:**
1. Ensure `CROSS_SITE_COOKIES=true` on Render backend
2. Verify `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` match your Netlify URL (include `https://`)
3. Clear browser cookies and cache
4. Check browser console for CORS errors
5. Verify `VITE_API_URL` is set correctly on Netlify (no trailing slash)

### Login works but subsequent requests fail
**Solutions:**
1. Check if session cookie is being sent: Open DevTools > Application > Cookies
2. Verify `SESSION_COOKIE_SECURE=true` in production (set automatically by Django when `DEBUG=false`)
3. Ensure frontend sends `withCredentials: true` for all API calls

### CORS errors in browser console
**Solutions:**
1. Verify `CORS_ALLOWED_ORIGINS` matches exact Netlify URL
2. Ensure `CORS_ALLOW_CREDENTIALS=true` in Django settings (already set)
3. Check if URL has trailing slash (should not)

### Cookies not being set (Samesite issues)
**Solutions:**
1. Verify `CROSS_SITE_COOKIES=true` on Render backend
2. Check Django settings:
   - `SESSION_COOKIE_SAMESITE=None`
   - `CSRF_COOKIE_SAMESITE=None`
   - `SESSION_COOKIE_SECURE=true`
   - `CSRF_COOKIE_SECURE=true`
3. Clear ALL cookies for both domains and retry

## Security Notes

1. **Never use `@csrf_exempt` in production** unless absolutely necessary (webhooks etc.)
2. **Always validate CSRF tokens** for state-changing operations (POST, PATCH, DELETE)
3. **Use HTTPS** in production (required for secure cookies)
4. **Keep `DEBUG=false`** in production
5. **Regenerate secret keys** if compromised

## Local Development

For local development, the setup is already configured:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- CORS and CSRF settings allow both localhost origins
- Vite proxy handles API requests in development mode

## Files Modified

1. `core/views.py` - Removed `@csrf_exempt`, added security comments
2. `breathe_esg_frontend/src/api/client.js` - Added CSRF token fetching and caching

## Verification Checklist

- [ ] Backend deployed on Render
- [ ] Frontend deployed on Netlify
- [ ] `VITE_API_URL` set on Netlify
- [ ] `CORS_ALLOWED_ORIGINS` set on Render (matches Netlify URL)
- [ ] `CSRF_TRUSTED_ORIGINS` set on Render (matches Netlify URL)
- [ ] `CROSS_SITE_COOKIES=true` on Render
- [ ] Backend redeployed after environment variable changes
- [ ] Login works with `admin` / `admin123`
- [ ] Can navigate to Analytics page after login
- [ ] Can upload CSV files
- [ ] Can approve/reject records
- [ ] Session persists across page refreshes

## Support

If issues persist:
1. Share backend logs from Render (Logs tab)
2. Share browser console errors (including network tab)
3. Verify all environment variables match exactly (no typos)
4. Test with different browsers (Chrome, Firefox, Safari)
5. Check for browser extensions blocking cookies
