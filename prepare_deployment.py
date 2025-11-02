"""
VIKRANTA MVP - Production Preparation Script
This script prepares your project for deployment
"""

import os
import secrets
import json
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key for production"""
    return secrets.token_urlsafe(32)

def create_env_production():
    """Create production environment files"""
    
    print("🔧 Creating production environment files...")
    
    # Backend .env.production
    backend_env = f"""# VIKRANTA Backend - Production Environment
FLASK_ENV=production
SECRET_KEY={generate_secret_key()}

# Database (Will be provided by Railway)
DATABASE_URL=postgresql://user:password@host:port/database

# External APIs
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
TWILIO_ACCOUNT_SID=your_twilio_sid_here
TWILIO_AUTH_TOKEN=your_twilio_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_here
GEMINI_API_KEY=your_gemini_key_here

# CORS (Update with your frontend URL)
CORS_ORIGIN=https://vikranta-frontend.railway.app

# Server
PORT=5000
"""
    
    backend_path = Path("backend/.env.production")
    backend_path.write_text(backend_env)
    print(f"✅ Created: {backend_path}")
    
    # Frontend .env.production
    frontend_env = """# VIKRANTA Frontend - Production Environment
VITE_API_URL=https://vikranta-backend.railway.app
VITE_MAPBOX_TOKEN=your_mapbox_token_here
"""
    
    frontend_path = Path("frontend/.env.production")
    frontend_path.write_text(frontend_env)
    print(f"✅ Created: {frontend_path}")
    
    print("\n⚠️  IMPORTANT: Update the placeholder values with your actual credentials!")
    print("📝 Never commit .env.production to Git!\n")

def create_gitignore():
    """Create comprehensive .gitignore"""
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log
yarn-error.log
.pnpm-debug.log

# Environment files
.env
.env.local
.env.production
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Docker
docker-compose.override.yml

# Build
dist/
build/
.cache/

# Testing
.coverage
htmlcov/
.pytest_cache/

# Misc
.DS_Store
Thumbs.db
"""
    
    gitignore_path = Path(".gitignore")
    gitignore_path.write_text(gitignore_content)
    print(f"✅ Created: {gitignore_path}")

def add_health_endpoint():
    """Instructions to add health check endpoint"""
    
    health_code = """
# Add this to backend/app.py (after routes registration)

@app.route('/health')
def health_check():
    '''Health check endpoint for monitoring'''
    from datetime import datetime
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'vikranta-backend',
        'version': '1.0.0'
    }

@app.route('/api/health')
def api_health_check():
    '''API health check with database connectivity'''
    from datetime import datetime
    try:
        # Test database connection
        from extensions import db
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'service': 'vikranta-backend',
        'version': '1.0.0'
    }
"""
    
    print("\n📋 Add this health check endpoint to backend/app.py:")
    print(health_code)

def update_requirements():
    """Add production dependencies"""
    
    prod_deps = """
# Add these to backend/requirements.txt

# Production WSGI Server
gunicorn==21.2.0
eventlet==0.33.3

# Compression
flask-compress==1.14

# Rate Limiting (Optional but recommended)
flask-limiter==3.5.0

# Monitoring (Optional)
# sentry-sdk[flask]==1.39.1
"""
    
    print("\n📦 Add these to backend/requirements.txt:")
    print(prod_deps)

def create_railway_config():
    """Create railway.json configuration"""
    
    railway_config = {
        "$schema": "https://railway.app/railway.schema.json",
        "build": {
            "builder": "DOCKERFILE",
            "dockerfilePath": "Dockerfile"
        },
        "deploy": {
            "numReplicas": 1,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 10
        }
    }
    
    # Backend railway.json
    backend_railway_path = Path("backend/railway.json")
    backend_railway_path.write_text(json.dumps(railway_config, indent=2))
    print(f"✅ Created: {backend_railway_path}")
    
    # Frontend railway.json
    frontend_railway_path = Path("frontend/railway.json")
    frontend_railway_path.write_text(json.dumps(railway_config, indent=2))
    print(f"✅ Created: {frontend_railway_path}")

def create_deployment_checklist():
    """Create interactive deployment checklist"""
    
    checklist = """# 🚀 VIKRANTA DEPLOYMENT CHECKLIST

## Pre-Deployment
- [ ] All tests passing locally
- [ ] Debug mode disabled (app.py: debug=False)
- [ ] Environment variables documented
- [ ] Sensitive data removed from code
- [ ] .gitignore configured
- [ ] Health check endpoints added
- [ ] Gunicorn added to requirements.txt

## GitHub Setup
- [ ] Repository created on GitHub
- [ ] Code pushed to main branch
- [ ] .env files NOT committed (check .gitignore)
- [ ] README updated with project info

## Railway Setup
- [ ] Railway account created
- [ ] PostgreSQL database provisioned
- [ ] PostGIS extension enabled on database
- [ ] Backend service deployed
- [ ] Frontend service deployed
- [ ] All environment variables set

## Testing
- [ ] Frontend loads without errors
- [ ] Backend /health endpoint responds
- [ ] Login/Register works
- [ ] Map displays correctly
- [ ] WebSocket connects
- [ ] SOS alert flows work
- [ ] Mobile responsive
- [ ] HTTPS enabled

## Post-Deployment
- [ ] Monitoring configured
- [ ] Uptime checks setup
- [ ] Team notified of URLs
- [ ] Documentation updated
- [ ] Backup strategy in place

## URLs to Share
- Frontend: https://vikranta-frontend.railway.app
- Backend: https://vikranta-backend.railway.app
- Health: https://vikranta-backend.railway.app/health

## Credentials Document
Create a secure document with:
- Admin login credentials
- API keys (Mapbox, Twilio, Gemini)
- Database connection string
- Railway login details
"""
    
    checklist_path = Path("DEPLOYMENT-CHECKLIST.md")
    checklist_path.write_text(checklist)
    print(f"✅ Created: {checklist_path}")

def main():
    """Main execution"""
    print("=" * 60)
    print("🚀 VIKRANTA MVP - PRODUCTION PREPARATION")
    print("=" * 60)
    print()
    
    try:
        # Create all necessary files
        create_gitignore()
        create_env_production()
        create_railway_config()
        create_deployment_checklist()
        
        print("\n" + "=" * 60)
        print("✅ PREPARATION COMPLETE!")
        print("=" * 60)
        
        # Additional instructions
        print("\n📋 NEXT STEPS:")
        print("1. Update .env.production files with your actual credentials")
        print("2. Review DEPLOYMENT-CHECKLIST.md")
        print("3. Follow DEPLOYMENT-GUIDE.md for step-by-step deployment")
        
        update_requirements()
        add_health_endpoint()
        
        print("\n🎯 Your project is ready for deployment!")
        print("📖 Read DEPLOYMENT-GUIDE.md for complete instructions")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please run this script from the vikranta-mvp directory")

if __name__ == "__main__":
    main()
