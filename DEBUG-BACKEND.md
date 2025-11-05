# Quick Debug Script - Check Backend Endpoints

Run these commands in PowerShell to test backend directly:

```powershell
# Test 1: Check if backend is alive
curl https://vikranta-mvp-production.up.railway.app/api/health

# Test 2: Check geofence list (should return empty array if no zones)
curl https://vikranta-mvp-production.up.railway.app/api/geofence/list?active=true

# Test 3: Check if GEMINI_API_KEY is being read (this will fail but show error message)
# You need to check Railway logs for this
```

## Railway Logs - What to Check:

1. Go to Railway → Backend Service → Logs tab
2. Look for these errors when cultural/nearby is called:
   - `GEMINI_API_KEY not configured`
   - `KeyError` or `AttributeError`
   - Gemini API response errors

## Most Likely Issues:

### Issue 1: GEMINI_API_KEY Format
The Gemini API key might need the full URL format:

**Current in Railway:**
```
GEMINI_API_KEY=AIzaSyBCSzQmAxHiBWGLS1_zVA0wI5TqtQI_faY
```

**Might need to be set in different format or the backend route is not reading it correctly.**

### Issue 2: Backend Route Error
The `/api/cultural/nearby` route might be crashing before even calling Gemini.

Let me check the backend code:
