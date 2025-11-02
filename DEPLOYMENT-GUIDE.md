# 🚀 VIKRANTA MVP - WEB DEPLOYMENT GUIDE

**Date:** November 2, 2025  
**Project:** VIKRANTA Smart Tourist Safety System  
**Goal:** Deploy to production web hosting

---

## 📋 TABLE OF CONTENTS

1. [Deployment Options](#deployment-options)
2. [Recommended Approach](#recommended-approach)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Domain & SSL Setup](#domain-ssl-setup)
6. [Post-Deployment Tasks](#post-deployment-tasks)
7. [Monitoring & Maintenance](#monitoring-maintenance)

---

## 1️⃣ DEPLOYMENT OPTIONS

### Option A: Free/Low-Cost (Recommended for MVP/Demo)

| Platform | Frontend | Backend | Database | Cost | Best For |
|----------|----------|---------|----------|------|----------|
| **Render** | ✅ Yes | ✅ Yes | ✅ PostgreSQL | Free tier | MVP Demo |
| **Railway** | ✅ Yes | ✅ Yes | ✅ PostgreSQL | $5/month | Production-ready |
| **Vercel + Railway** | ✅ Yes | ❌ No | ❌ No | Free + $5 | Fast frontend |
| **Heroku** | ✅ Yes | ✅ Yes | ✅ PostgreSQL | $7/month | Traditional |

### Option B: Cloud Providers (Scalable Production)

| Platform | Frontend | Backend | Database | Cost | Best For |
|----------|----------|---------|----------|------|----------|
| **AWS (Elastic Beanstalk)** | ✅ Yes | ✅ Yes | ✅ RDS | ~$20/month | Enterprise |
| **Google Cloud Run** | ✅ Yes | ✅ Yes | ✅ Cloud SQL | ~$15/month | Auto-scaling |
| **DigitalOcean** | ✅ Yes | ✅ Yes | ✅ Managed DB | ~$12/month | Simple setup |
| **Azure** | ✅ Yes | ✅ Yes | ✅ Azure DB | ~$20/month | Microsoft stack |

### Option C: VPS (Full Control)

| Platform | Specs | Cost | Best For |
|----------|-------|------|----------|
| **DigitalOcean Droplet** | 2GB RAM, 1 vCPU | $12/month | Full control |
| **Linode** | 2GB RAM, 1 vCPU | $10/month | Developer-friendly |
| **AWS EC2** | t3.small | ~$15/month | AWS ecosystem |
| **Vultr** | 2GB RAM | $10/month | Fast deployment |

---

## 2️⃣ RECOMMENDED APPROACH (FOR YOUR PROJECT)

### 🏆 **Best Choice: Railway.app**

**Why Railway?**
- ✅ Free $5 credit monthly (enough for MVP)
- ✅ Supports Docker Compose (your current setup)
- ✅ Built-in PostgreSQL with PostGIS support
- ✅ Automatic HTTPS/SSL certificates
- ✅ WebSocket support (critical for your app)
- ✅ Easy GitHub integration (auto-deploy)
- ✅ No credit card required for trial
- ✅ Simple dashboard, perfect for demos

**What You'll Get:**
```
Frontend:  https://vikranta-frontend.railway.app
Backend:   https://vikranta-backend.railway.app
Database:  Managed PostgreSQL with PostGIS
Cost:      FREE (with $5/month credit)
```

---

## 3️⃣ PRE-DEPLOYMENT CHECKLIST

### ✅ Code Preparation

- [ ] **Remove Debug Mode**
  ```python
  # backend/app.py
  if __name__ == '__main__':
      app, socketio = create_app()
      socketio.run(app, host='0.0.0.0', port=5000, debug=False)  # ← Set to False
  ```

- [ ] **Add Production Environment Variables**
  ```bash
  # Create .env.production file
  FLASK_ENV=production
  SECRET_KEY=<generate-strong-key>
  DATABASE_URL=<will-be-provided-by-railway>
  MAPBOX_ACCESS_TOKEN=<your-token>
  TWILIO_ACCOUNT_SID=<your-sid>
  TWILIO_AUTH_TOKEN=<your-token>
  TWILIO_PHONE_NUMBER=<your-number>
  GEMINI_API_KEY=<your-key>
  CORS_ORIGIN=https://vikranta-frontend.railway.app
  ```

- [ ] **Update Frontend API URL**
  ```javascript
  // frontend/src/services/api.js
  const BACKEND_URL = import.meta.env.PROD 
    ? 'https://vikranta-backend.railway.app'
    : 'http://localhost:5000';
  ```

- [ ] **Add Health Check Endpoint**
  ```python
  # backend/app.py
  @app.route('/health')
  def health_check():
      return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
  ```

- [ ] **Optimize Dockerfiles for Production**
  ```dockerfile
  # backend/Dockerfile
  FROM python:3.11-slim
  ENV PYTHONUNBUFFERED=1
  ENV PYTHONDONTWRITEBYTECODE=1
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  EXPOSE 5000
  CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:app"]
  ```

- [ ] **Add Gunicorn to requirements.txt**
  ```
  gunicorn==21.2.0
  eventlet==0.33.3
  ```

### ✅ Security Hardening

- [ ] **Generate Strong Secret Key**
  ```python
  import secrets
  print(secrets.token_urlsafe(32))  # Use this for SECRET_KEY
  ```

- [ ] **Update CORS Settings**
  ```python
  # backend/config.py
  CORS_ORIGINS = [
      'https://vikranta-frontend.railway.app',
      'https://your-custom-domain.com'
  ]
  ```

- [ ] **Add Rate Limiting**
  ```python
  from flask_limiter import Limiter
  
  limiter = Limiter(
      app,
      key_func=lambda: request.headers.get('X-Forwarded-For', request.remote_addr),
      default_limits=["200 per day", "50 per hour"]
  )
  ```

### ✅ Database Preparation

- [ ] **Add Migration Scripts** (if using Flask-Migrate)
  ```bash
  pip install Flask-Migrate
  ```

- [ ] **Backup Local Data** (if any test data to preserve)
  ```bash
  docker exec vikranta_db pg_dump -U vikranta vikranta_db > backup.sql
  ```

---

## 4️⃣ STEP-BY-STEP DEPLOYMENT (Railway.app)

### Step 1: Prepare Your Repository

```bash
# 1. Initialize git (if not already done)
cd c:\Users\Kiran\OneDrive\Desktop\Pvikranta\vikranta-mvp
git init

# 2. Create .gitignore
echo "node_modules/
__pycache__/
*.pyc
.env
.env.local
.env.production
*.log
.DS_Store
.vscode/
*.db" > .gitignore

# 3. Commit your code
git add .
git commit -m "Initial commit - VIKRANTA MVP ready for deployment"

# 4. Create GitHub repository
# Go to https://github.com/new
# Repository name: vikranta-mvp
# Make it Public (for free hosting)

# 5. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/vikranta-mvp.git
git branch -M main
git push -u origin main
```

### Step 2: Sign Up for Railway

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Authorize Railway to access your repositories

### Step 3: Deploy Database First

```bash
# In Railway dashboard:
1. Click "+ New Project"
2. Select "Provision PostgreSQL"
3. Wait for deployment (1-2 minutes)
4. Click on PostgreSQL service
5. Go to "Connect" tab
6. Enable "PostGIS" plugin:
   - Click "Variables"
   - Add: POSTGRES_EXTENSIONS=postgis
   - Restart database
7. Copy DATABASE_URL (you'll need this)
```

### Step 4: Deploy Backend

```bash
# In Railway dashboard:
1. Click "+ New Service"
2. Select "GitHub Repo"
3. Choose "vikranta-mvp" repository
4. Select "backend" folder as root directory
5. Railway auto-detects Dockerfile
6. Add environment variables:
   - DATABASE_URL: <paste from PostgreSQL service>
   - SECRET_KEY: <generate with secrets.token_urlsafe(32)>
   - MAPBOX_ACCESS_TOKEN: <your token>
   - TWILIO_ACCOUNT_SID: <your sid>
   - TWILIO_AUTH_TOKEN: <your token>
   - TWILIO_PHONE_NUMBER: <your number>
   - GEMINI_API_KEY: <your key>
   - FLASK_ENV: production
   - PORT: 5000
7. Click "Deploy"
8. Wait 3-5 minutes
9. Copy the public URL (e.g., vikranta-backend.railway.app)
```

### Step 5: Deploy Frontend

```bash
# First, update frontend API URL
# Create frontend/.env.production

VITE_API_URL=https://vikranta-backend.railway.app
VITE_MAPBOX_TOKEN=<your-mapbox-token>

# In Railway dashboard:
1. Click "+ New Service"
2. Select "GitHub Repo"
3. Choose "vikranta-mvp" repository
4. Select "frontend" folder as root directory
5. Add environment variables:
   - VITE_API_URL: https://vikranta-backend.railway.app
   - VITE_MAPBOX_TOKEN: <your token>
6. Click "Deploy"
7. Wait 3-5 minutes
8. Copy the public URL (e.g., vikranta-frontend.railway.app)
```

### Step 6: Initialize Database

```bash
# Connect to Railway PostgreSQL and run migrations
# Option 1: Use Railway CLI
railway login
railway link
railway run python backend/models/__init__.py  # Or your init script

# Option 2: Use Railway Web Console
1. Go to PostgreSQL service
2. Click "Query" tab
3. Run your schema SQL:

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'tourist',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add other tables (incidents, geofences, etc.)
```

---

## 5️⃣ DOMAIN & SSL SETUP

### Option A: Use Railway Subdomain (Free)

```
✅ Already done! Railway provides:
- vikranta-frontend.railway.app (Free SSL)
- vikranta-backend.railway.app (Free SSL)
```

### Option B: Custom Domain (Professional)

**1. Buy a Domain**
- Namecheap.com (~$10/year for .com)
- Google Domains (~$12/year)
- GoDaddy (~$15/year)

**Example:** `vikranta.in` or `vikranta-safety.com`

**2. Configure DNS in Railway**

```bash
# In Railway dashboard:
1. Go to Frontend service
2. Click "Settings" → "Domains"
3. Click "Add Custom Domain"
4. Enter: vikranta.in (or www.vikranta.in)
5. Railway shows DNS records to add

# In your domain registrar (Namecheap/GoDaddy):
1. Go to DNS settings
2. Add these records:
   
   Type: CNAME
   Host: www
   Value: vikranta-frontend.railway.app
   
   Type: A
   Host: @
   Value: <IP provided by Railway>

3. Wait 1-24 hours for DNS propagation
4. Railway auto-enables SSL (Let's Encrypt)
```

**3. Update Frontend to Use Custom Domain**

```javascript
// frontend/src/services/api.js
const BACKEND_URL = import.meta.env.PROD 
  ? 'https://api.vikranta.in'  // Or your backend domain
  : 'http://localhost:5000';
```

**4. Configure Backend Custom Domain**

```bash
# Same process for backend:
1. Add subdomain: api.vikranta.in
2. Point to vikranta-backend.railway.app
3. Update CORS in backend:

CORS(app, origins=[
    'https://vikranta.in',
    'https://www.vikranta.in'
])
```

---

## 6️⃣ POST-DEPLOYMENT TASKS

### ✅ Verify Deployment

**1. Test Frontend**
```bash
# Visit: https://vikranta-frontend.railway.app
# Check:
- [ ] Page loads without errors
- [ ] Login works
- [ ] Map displays correctly
- [ ] No console errors (F12)
```

**2. Test Backend**
```bash
# Visit: https://vikranta-backend.railway.app/health
# Should return: {"status": "healthy", "timestamp": "..."}

# Test API endpoints:
curl https://vikranta-backend.railway.app/api/geofence/list
```

**3. Test WebSocket**
```bash
# Open browser console on frontend
# Should see:
✅ Tourist connected to WebSocket
✅ Successfully joined user room
```

**4. Test Full Flow**
```bash
- [ ] Register new user
- [ ] Login
- [ ] View map and geofences
- [ ] Click SOS (tourist)
- [ ] Receive alert (authority)
- [ ] Send acknowledgment
- [ ] Verify notification (tourist)
```

### ✅ Performance Optimization

**1. Enable Gzip Compression**
```python
# backend/app.py
from flask_compress import Compress

compress = Compress()
compress.init_app(app)
```

**2. Add Caching Headers**
```python
@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static'):
        response.cache_control.max_age = 31536000  # 1 year
    return response
```

**3. Frontend Build Optimization**
```javascript
// frontend/vite.config.js
export default {
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true  // Remove console.logs in production
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'map-vendor': ['mapbox-gl']
        }
      }
    }
  }
}
```

### ✅ Security Checklist

- [ ] **HTTPS Enabled** (Railway auto-enables)
- [ ] **Environment Variables Set** (no hardcoded secrets)
- [ ] **CORS Configured** (only allow your domains)
- [ ] **Rate Limiting Added** (prevent abuse)
- [ ] **SQL Injection Protected** (using SQLAlchemy ORM)
- [ ] **XSS Protection** (React auto-escapes)
- [ ] **JWT Tokens** (already implemented)
- [ ] **Input Validation** (check all forms)

### ✅ SEO & Metadata

```html
<!-- frontend/index.html -->
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>VIKRANTA - Smart Tourist Safety System | SIH 2025</title>
  <meta name="description" content="VIKRANTA: AI-powered tourist safety system with real-time geofencing, emergency alerts, and cultural guidance for Bangalore." />
  <meta name="keywords" content="tourist safety, emergency alert, geofencing, Bangalore tourism, SIH 2025" />
  <meta property="og:title" content="VIKRANTA Smart Tourist Safety System" />
  <meta property="og:description" content="Real-time safety monitoring for tourists" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://vikranta.in" />
  <link rel="canonical" href="https://vikranta.in" />
</head>
```

---

## 7️⃣ MONITORING & MAINTENANCE

### ✅ Set Up Monitoring

**1. Railway Dashboard**
```bash
# Built-in metrics:
- CPU usage
- Memory usage
- Request count
- Response times
- Error logs
```

**2. Error Tracking (Optional)**
```bash
# Add Sentry for error tracking
pip install sentry-sdk[flask]

# backend/app.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

**3. Uptime Monitoring**
```bash
# Use free services:
- UptimeRobot.com (free, 50 monitors)
- Better Uptime (free tier)
- Pingdom (limited free)

Monitor these URLs:
- https://vikranta-frontend.railway.app
- https://vikranta-backend.railway.app/health
```

### ✅ Backup Strategy

**1. Database Backups**
```bash
# Railway auto-backups PostgreSQL
# Manual backup:
railway pg:dump > backup_$(date +%Y%m%d).sql
```

**2. Code Backups**
```bash
# Already backed up on GitHub
# Create releases for versions:
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0
```

### ✅ Logging

**1. Centralized Logging**
```python
# backend/app.py
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/app.log', maxBytes=10000000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
```

**2. View Railway Logs**
```bash
# Install Railway CLI
npm i -g @railway/cli

# View logs
railway logs --service backend
railway logs --service frontend
```

---

## 8️⃣ COST BREAKDOWN

### Railway (Recommended)

| Service | Usage | Cost |
|---------|-------|------|
| **Hobby Plan** | $5 free credit/month | $0 |
| **PostgreSQL** | 1GB storage, 100MB RAM | Included |
| **Backend** | 512MB RAM, 0.5 vCPU | ~$2/month |
| **Frontend** | Static hosting | ~$0.50/month |
| **Bandwidth** | 100GB/month | Included |
| **SSL Certificates** | Unlimited | Free |
| **Total** | With free credit | **$0 - $2.50/month** |

### Custom Domain (Optional)

| Item | Cost |
|------|------|
| `.com` domain | $10/year |
| `.in` domain | $8/year |
| `.app` domain | $15/year |

### External Services

| Service | Purpose | Cost |
|---------|---------|------|
| Mapbox | Maps (50k loads/month) | Free |
| Twilio | SMS (Trial) | Free |
| Google Gemini | AI (60 req/min) | Free |

**Total Monthly Cost: $0 - $3/month** ✅

---

## 9️⃣ SCALING STRATEGY

### Phase 1: MVP/Demo (Current)
```
Users:     10-50 concurrent
Traffic:   <1000 req/hour
Cost:      Free - $5/month
Platform:  Railway Free Tier
```

### Phase 2: Beta Launch (100-500 users)
```
Users:     100-500 concurrent
Traffic:   5000-10000 req/hour
Cost:      $20-30/month
Platform:  Railway Pro + CDN
Upgrades:  
  - Add Redis for caching
  - Enable CDN (Cloudflare Free)
  - Upgrade to 2GB RAM backend
```

### Phase 3: Production (1000+ users)
```
Users:     1000+ concurrent
Traffic:   50000+ req/hour
Cost:      $100-200/month
Platform:  AWS/GCP with auto-scaling
Upgrades:
  - Load balancer
  - Multiple backend instances
  - Managed PostgreSQL
  - Full monitoring stack
```

---

## 🔟 TROUBLESHOOTING

### Issue: "WebSocket connection failed"
```bash
Solution:
1. Enable WebSocket in Railway:
   - Go to service settings
   - Enable "WebSocket support"
2. Check CORS headers include WebSocket
3. Verify Socket.IO version matches frontend/backend
```

### Issue: "Database connection error"
```bash
Solution:
1. Check DATABASE_URL environment variable
2. Ensure PostGIS extension is enabled
3. Verify database is running in Railway dashboard
4. Check connection string format
```

### Issue: "Map not loading"
```bash
Solution:
1. Verify Mapbox token is set in frontend
2. Check CORS allows your domain
3. Verify token has correct scopes in Mapbox dashboard
```

### Issue: "502 Bad Gateway"
```bash
Solution:
1. Check backend logs for crashes
2. Increase backend memory in Railway
3. Verify PORT environment variable
4. Check if database is responsive
```

---

## ✅ DEPLOYMENT CHECKLIST

### Pre-Deployment
- [ ] Code tested locally
- [ ] Debug mode disabled
- [ ] Environment variables documented
- [ ] Sensitive data removed from code
- [ ] .gitignore configured
- [ ] README updated with deployment info

### During Deployment
- [ ] GitHub repository created and pushed
- [ ] Railway account created
- [ ] PostgreSQL provisioned with PostGIS
- [ ] Backend deployed with all env vars
- [ ] Frontend deployed with API URL
- [ ] Database initialized with schema
- [ ] Custom domain configured (if applicable)

### Post-Deployment
- [ ] All pages load without errors
- [ ] Authentication works
- [ ] Map displays correctly
- [ ] WebSocket connects successfully
- [ ] SOS alerts work end-to-end
- [ ] Mobile responsive
- [ ] HTTPS enabled
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Documentation updated

---

## 📞 QUICK START COMMANDS

```bash
# 1. Prepare code for deployment
git add .
git commit -m "Production ready"
git push origin main

# 2. Install Railway CLI
npm install -g @railway/cli

# 3. Login to Railway
railway login

# 4. Link project
railway link

# 5. Deploy
railway up

# 6. View logs
railway logs

# 7. Open in browser
railway open
```

---

## 🎯 NEXT STEPS

1. **Complete Pre-Deployment Checklist** (Section 3)
2. **Push Code to GitHub** (Step 1 in Section 4)
3. **Deploy to Railway** (Steps 2-5 in Section 4)
4. **Test Everything** (Section 6)
5. **Share Your Link!** 🚀

---

## 📚 ADDITIONAL RESOURCES

- [Railway Documentation](https://docs.railway.app)
- [Flask Production Guide](https://flask.palletsprojects.com/en/stable/deploying/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)
- [Custom Domains on Railway](https://docs.railway.app/deploy/deployments#custom-domains)

---

**Need Help?**
- Railway Discord: https://discord.gg/railway
- Stack Overflow: Tag with `railway`, `flask`, `react`
- GitHub Issues: Create in your repository

---

**Status:** 📝 **READY TO DEPLOY**  
**Estimated Time:** 30-60 minutes for first deployment  
**Difficulty:** ⭐⭐☆☆☆ (Beginner-Intermediate)

**Good luck with your deployment! 🚀**

