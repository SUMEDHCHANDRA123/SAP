# CSRF Token Fix - Summary

## Problem
"CSRF token missing" error when logging into your Django + React app deployed on Render (backend) and Netlify (frontend).

## Root Causes
1. Backend used `@csrf_exempt` decorator which disabled CSRF protection (security issue)
2. Frontend didn't fetch CSRF token before login
3. Cross-origin setup requires special cookie settings (SameSite=None)

## Changes Made

### Backend (Django - core/views.py)
- **Removed** `@csrf_exempt` from:
  - `AuthMeView.post()` (login endpoint)
  - `AuthMeView.delete()` (logout endpoint)
  - `AuthRegisterView.post()` (registration endpoint)
- **Kept** `@ensure_csrf_cookie` on `AuthMeView.get()` to set CSRF cookie
- Added security comments

### Frontend (React - breathe_esg_frontend/src/api/client.js)
- **Added** `fetchCsrfToken()` function to pre-fetch CSRF token
- **Updated** `loginSession()` to fetch CSRF token before login
- **Updated** `registerUser()` to fetch CSRF token before registration
- **Added** CSRF token caching in localStorage

## Deployment Requirements

### Render (Backend) - MUST set these:
```bash
CORS_ALLOWED_ORIGINS=https://your-netlify-app.netlify.app
CSRF_TRUSTED_ORIGINS=https://your-netlify-app.netlify.app
CROSS_SITE_COOKIES=true
DJANGO_DEBUG=false
```

### Netlify (Frontend) - MUST set:
```bash
VITE_API_URL=https://your-render-app.onrender.com
```

## How the Fix Works

1. **User visits Netlify frontend** → React app loads
2. **Frontend fetches CSRF token**:
   - Calls `GET /api/auth/me/` (before login)
   - Django sets `csrftoken` cookie via `@ensure_csrf_cookie`
   - Frontend extracts token and stores in localStorage
3. **User submits login form**:
   - Frontend sends `POST /api/auth/me/` with:
     - `X-CSRFToken` header (from localStorage)
     - Username/password in body
     - `withCredentials: true` (sends cookies)
4. **Django validates**:
   - Checks CSRF token in header
   - Authenticates user
   - Sets session cookie
5. **Login successful** → User redirected to dashboard

## Key Security Improvements

1. **CSRF protection re-enabled** for all auth endpoints
2. **Cross-site cookies properly configured** (SameSite=None, Secure=true)
3. **Token caching** reduces unnecessary API calls
4. **No token exposure** (not in URL, only in headers)

## Files Modified

- `core/views.py` - Removed csrf exemptions
- `breathe_esg_frontend/src/api/client.js` - Added CSRF token fetching

## Documentation Created

- `CSRF_FIX_DEPLOYMENT.md` - Complete deployment guide
- `ENV_VARS_QUICK_REFERENCE.md` - Critical env vars checklist
- `FIX_SUMMARY.md` - This file

## Next Steps

1. **Commit and push** these changes to GitHub
2. **Update environment variables** on Render and Netlify (see above)
3. **Redeploy backend** on Render
4. **Redeploy frontend** on Netlify (if needed)
5. **Clear browser cookies** for both domains
6. **Test login** with `admin` / `admin123`

## Verification

After deployment, verify:
- ✅ Login works without CSRF errors
- ✅ Can navigate to Analytics page
- ✅ Can upload CSV files
- ✅ Can approve/reject records
- ✅ Session persists across page refreshes
- ✅ Logout works correctly

## Support

If issues persist:
1. Share Render backend logs
2. Share browser console errors
3. Verify all environment variables match exactly
4. Check browser DevTools > Application > Cookies

## Security Best Practices

- ✅ Never disable CSRF in production
- ✅ Always use HTTPS in production
- ✅ Regenerate secret keys if compromised
- ✅ Keep DEBUG=false in production
- ✅ Validate all user inputs

## Local Development

No changes needed - works out of the box:
- Vite proxy handles API requests
- CORS/CSRF settings allow localhost
- Both frontend and backend on same origin (localhost)

## Rollback Plan

If issues arise, you can temporarily:
1. Set `DJANGO_DEBUG=true` to see detailed errors
2. Check browser DevTools for cookie/security issues
3. Test with different browsers
4. Revert to previous commit if critical issues found

**Remember to set DEBUG=false after testing!**
