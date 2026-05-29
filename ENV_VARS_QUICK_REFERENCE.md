# Critical Environment Variables for CSRF Fix

## Render (Backend - breathe-esg-api)

```bash
# MUST set these for CSRF to work with Netlify
CORS_ALLOWED_ORIGINS=https://your-netlify-app.netlify.app
CSRF_TRUSTED_ORIGINS=https://your-netlify-app.netlify.app
CROSS_SITE_COOKIES=true

# Production security
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<generate-secure-key>

# Auto-configured by Render
DATABASE_URL=<from-postgres-service>
CELERY_BROKER_URL=<from-redis-service>
CELERY_RESULT_BACKEND=<from-redis-service>
```

## Netlify (Frontend)

```bash
# Backend API URL (NO trailing slash)
VITE_API_URL=https://your-render-app.onrender.com
```

## Quick Fix Steps

1. **Set environment variables on both platforms**
2. **Redeploy backend** on Render
3. **Clear browser cookies** for both domains
4. **Test login**

## Verify Settings

```bash
# Check CSRF cookie is set (browser DevTools)
Application > Cookies > https://your-render-app.onrender.com
Should see: csrftoken cookie with HttpOnly=false, Secure=true, SameSite=None

# Check session cookie
Should see: sessionid cookie with HttpOnly=true, Secure=true, SameSite=None

# Check request headers
Network tab > Request Headers
Should see: X-CSRFToken: <token-value>
```

## Common Mistakes

❌ Trailing slash in URLs:
- `https://app.netlify.app/` ❌
- `https://app.netlify.app` ✅

❌ Missing `https://`:
- `app.netlify.app` ❌
- `https://app.netlify.app` ✅

❌ Wrong environment variable name:
- `CORS_ORIGIN` ❌
- `CORS_ALLOWED_ORIGINS` ✅

❌ Missing `CROSS_SITE_COOKIES`:
- If not set, cookies default to SameSite=Lax (won't work cross-origin)
- Set to `true` for SameSite=None ✅

## Test Login Locally

```bash
# Start backend
python manage.py runserver

# Start frontend
cd breathe_esg_frontend && npm run dev

# Open http://localhost:5173
# Login with admin/admin123
```

If local login works but deployed login fails, it's 100% an environment variable issue.

## Debug Mode

Temporarily enable debug on backend to see detailed CSRF errors:

```bash
# On Render, temporarily set:
DJANGO_DEBUG=true
```

**Remember to set back to `false` after debugging!**

## Browser Support

Tested on:
- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+

Safari may require allowing cross-site tracking:
Settings > Privacy > Prevent Cross-Site Tracking > OFF
