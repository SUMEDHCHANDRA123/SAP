# Deployment Checklist for CSRF Fix

## Pre-Deployment Checklist

- [ ] **Code changes committed to Git**
  - `core/views.py` - CSRF protection re-enabled
  - `breathe_esg_frontend/src/api/client.js` - CSRF token fetching added

- [ ] **Frontend builds successfully**
  ```bash
  cd breathe_esg_frontend
  npm run build
  ```
  Should complete without errors.

## Deployment Steps

### 1. Backend (Render)

- [ ] Go to Render Dashboard
- [ ] Select your backend service (breathe-esg-api)
- [ ] Navigate to **Environment** tab
- [ ] Set/Verify these variables:
  ```bash
  CORS_ALLOWED_ORIGINS=https://your-netlify-app.netlify.app
  CSRF_TRUSTED_ORIGINS=https://your-netlify-app.netlify.app
  CROSS_SITE_COOKIES=true
  DJANGO_DEBUG=false
  ```
- [ ] Click **Save Changes**
- [ ] Click **Manual Deploy** > **Deploy latest commit**
- [ ] Wait for deployment to complete (green checkmark)
- [ ] Note backend URL: `https://your-backend.onrender.com`

### 2. Frontend (Netlify)

- [ ] Go to Netlify Dashboard
- [ ] Select your site
- [ ] Navigate to **Site settings** > **Environment variables**
- [ ] Set/Verify:
  ```bash
  VITE_API_URL=https://your-backend.onrender.com
  ```
  **No trailing slash!**
- [ ] Trigger new deploy:
  - Option A: Push to Git (automatic)
  - Option B: **Deploys** > **Trigger deploy** > **Deploy site**
- [ ] Wait for deploy to complete
- [ ] Note frontend URL: `https://your-netlify-app.netlify.app`

### 3. Test Login

- [ ] Open browser in incognito/private mode
- [ ] Navigate to your Netlify URL
- [ ] Open DevTools (F12) > Application > Cookies
- [ ] Clear ALL cookies for both domains:
  - `your-backend.onrender.com`
  - `your-netlify-app.netlify.app`
- [ ] Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- [ ] Enter credentials: `admin` / `admin123`
- [ ] Click **Sign in**
- [ ] Should redirect to Analytics page (✅ SUCCESS)
- [ ] Check DevTools > Application > Cookies:
  - Should see `csrftoken` cookie (HttpOnly=false, Secure=true, SameSite=None)
  - Should see `sessionid` cookie (HttpOnly=true, Secure=true, SameSite=None)
- [ ] Navigate to **Upload** page
- [ ] Upload a sample CSV (from `sample_data/` directory)
- [ ] Should see success message
- [ ] Navigate to **History** page
- [ ] Should see new ingestion job
- [ ] Navigate to **Review** page
- [ ] Should see uploaded records
- [ ] Try approving a record
- [ ] Should work without errors

## Post-Deployment Security

- [ ] Change admin password:
  ```bash
  python manage.py changepassword admin
  ```
  (Or via Render shell)

- [ ] Set `RUN_SEED=false` on Render (only needed on first deploy)

- [ ] Verify `DJANGO_DEBUG=false` (should already be set)

- [ ] Check Django secret key is generated (not default):
  ```bash
  # On Render Environment tab
  DJANGO_SECRET_KEY=<should-be-long-random-string>
  ```
  If not set, generate one:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

## Troubleshooting

### "CSRF token missing" still appears

- [ ] Verify environment variables EXACTLY match (no typos)
- [ ] Check URLs have NO trailing slashes
- [ ] Ensure `CROSS_SITE_COOKIES=true` on Render
- [ ] Clear ALL browser cookies
- [ ] Try different browser
- [ ] Check Render logs for errors
- [ ] Temporarily enable `DJANGO_DEBUG=true` on Render for detailed errors

### CORS errors in console

- [ ] Verify `CORS_ALLOWED_ORIGINS` matches Netlify URL exactly
- [ ] Check protocol: must be `https://`
- [ ] No trailing slashes
- [ ] Redeploy backend after changing CORS settings

### Login works but can't upload files

- [ ] Check if CSRF token is being sent in upload requests
- [ ] Open DevTools > Network tab
- [ ] Find upload request
- [ ] Check Request Headers > `X-CSRFToken: <value>`
- [ ] If missing, check `breathe_esg_frontend/src/api/client.js` for errors

### Session lost on refresh

- [ ] Verify session cookie is set (DevTools > Application > Cookies)
- [ ] Check `SESSION_COOKIE_SECURE=true` (auto-set when DEBUG=false)
- [ ] Verify `withCredentials: true` in API client
- [ ] Check browser settings aren't blocking third-party cookies

## Success Criteria

- [ ] Login works without CSRF errors
- [ ] Can navigate between pages
- [ ] Can upload CSV files
- [ ] Can approve/reject records
- [ ] Session persists across page refreshes
- [ ] Logout works correctly
- [ ] No errors in browser console
- [ ] No errors in Render logs

## Rollback Plan

If critical issues found:

1. Revert Git commit
2. Redeploy both services
3. Set environment variables back to previous values
4. Clear browser cache and retry

## Support Resources

Documentation files created:
- `QUICK_START_FIX.md` - 3-step solution
- `CSRF_FIX_DEPLOYMENT.md` - Complete deployment guide
- `ENV_VARS_QUICK_REFERENCE.md` - Environment variables reference
- `FIX_SUMMARY.md` - Technical summary
- `DEPLOYMENT_CHECKLIST.md` - This file

## Production Monitoring

After successful deployment:

- [ ] Set up Render monitoring alerts
- [ ] Check periodically for CSRF errors in logs
- [ ] Monitor login success rates
- [ ] Test from different networks/devices
- [ ] Verify performance is acceptable (<2s login)

## Security Verification

- [ ] Verify HTTPS is enforced (redirects HTTP to HTTPS)
- [ ] Check cookies have Secure flag
- [ ] Verify SameSite=None for cross-origin cookies
- [ ] Confirm HttpOnly on session cookie (not CSRF cookie)
- [ ] Test CSRF token changes on each session
- [ ] Verify admin password is changed from default

## Final Sign-Off

- [ ] All tests pass
- [ ] Security checklist complete
- [ ] Documentation reviewed
- [ ] Team notified of successful deployment
- [ ] Monitoring configured
- [ ] Rollback plan documented

## Deployment Date: ____________
## Deployed By: ____________
## Backend Version: ____________
## Frontend Version: ____________
