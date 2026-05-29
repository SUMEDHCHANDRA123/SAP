# Quick Start - Fix CSRF Token Error

## Problem
"CSRF token missing" when logging into deployed app (Render backend + Netlify frontend).

## Solution - 3 Steps

### Step 1: Update Environment Variables

**On Render (backend service):**
```bash
CORS_ALLOWED_ORIGINS=https://YOUR-NETLIFY-APP.netlify.app
CSRF_TRUSTED_ORIGINS=https://YOUR-NETLIFY-APP.netlify.app
CROSS_SITE_COOKIES=true
```

**On Netlify (frontend):**
```bash
VITE_API_URL=https://YOUR-RENDER-APP.onrender.com
```

### Step 2: Redeploy Backend on Render
After setting environment variables, click "Manual Deploy" > "Deploy latest commit"

### Step 3: Test Login
1. Clear browser cookies for both domains
2. Open your Netlify URL
3. Login with `admin` / `admin123`

## That's it! Login should work now.

---

## What Changed?

**Backend:**
- Removed `@csrf_exempt` decorators (re-enabled CSRF protection)
- Kept `@ensure_csrf_cookie` to set CSRF token

**Frontend:**
- Added `fetchCsrfToken()` to get token before login
- Login now sends CSRF token in `X-CSRFToken` header

## If Still Not Working

Check these common issues:

1. **URL formatting:**
   - ❌ `https://app.netlify.app/` (trailing slash)
   - ✅ `https://app.netlify.app`

2. **Protocol:**
   - ❌ `app.netlify.app` (missing https)
   - ✅ `https://app.netlify.app`

3. **Environment variable names:**
   - ❌ `CORS_ORIGIN`
   - ✅ `CORS_ALLOWED_ORIGINS`

4. **Missing CROSS_SITE_COOKIES:**
   - Must be `true` for cross-origin setup

5. **Browser cache:**
   - Clear ALL cookies for both domains
   - Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

## Debug Mode

Temporarily enable Django debug logs:
```bash
# On Render
DJANGO_DEBUG=true
```
Check Render logs for detailed CSRF errors.
**Remember to set back to `false`!**

## Files Changed

1. `core/views.py` - Removed CSRF exemptions
2. `breathe_esg_frontend/src/api/client.js` - Added CSRF token fetching

## Next Steps After Fix

1. Change admin password: `python manage.py changepassword admin`
2. Set `RUN_SEED=false` on Render (after first deploy)
3. Test full flow: upload CSV → review → approve records

## Support

See full documentation:
- `CSRF_FIX_DEPLOYMENT.md` - Complete guide
- `ENV_VARS_QUICK_REFERENCE.md` - Environment variables
- `FIX_SUMMARY.md` - Technical summary
