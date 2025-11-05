# 🚀 Railway Environment Variables Setup

## ✅ REQUIRED Variables (Add these to Railway NOW)

Go to: Railway Dashboard → Your Backend Service → Variables Tab

### 1. **SendGrid Email (for OTP)**
```
SENDGRID_API_KEY=SG.<YOUR_SENDGRID_API_KEY_HERE>
SENDGRID_FROM_EMAIL=kiranbhanu671@gmail.com
```

**Note:** Use your actual SendGrid API key that starts with `SG.`

### 2. **Gemini AI (for Safety Zones & Cultural Places)**
```
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
```

**How to get Gemini API Key:**
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (starts with `AIza...`)
4. Paste it in Railway

### 3. **Twilio SMS (for Emergency SOS Alerts)**
```
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=<YOUR_TWILIO_ACCOUNT_SID>
TWILIO_AUTH_TOKEN=<YOUR_TWILIO_AUTH_TOKEN>
TWILIO_PHONE_NUMBER=<YOUR_TWILIO_PHONE_NUMBER>
```

**How to get Twilio credentials:**
1. Go to: https://www.twilio.com/console
2. Copy Account SID and Auth Token
3. Get a phone number from Twilio Console
4. Add to Railway

**OR** if you want to skip SMS for now:
```
SMS_ENABLED=false
```

### 4. **Frontend URL**
```
FRONTEND_URL=https://thorough-reflection-production-1bb6.up.railway.app
```

---

## 📋 Current Status

### ✅ Already Set:
- DATABASE_URL (PostgreSQL)
- JWT_SECRET_KEY
- SMTP_SERVER (smtp.sendgrid.net)
- SMTP_PORT (587)
- SMTP_USERNAME (apikey)
- SMTP_PASSWORD (your SendGrid API key - but needs SENDGRID_API_KEY too)

### ❌ Missing (causing errors):
- GEMINI_API_KEY ← **CRITICAL** (zones not loading)
- SENDGRID_API_KEY ← **CRITICAL** (OTP emails failing)
- TWILIO credentials ← **CRITICAL** (SOS SMS not sending)
- FRONTEND_URL ← Minor

---

## 🔧 After Adding Variables:

1. Railway will **auto-redeploy** backend (takes 2-3 minutes)
2. Check Railway logs for:
   - `✅ SET` next to Gemini API Key
   - No more "GEMINI_API_KEY: ❌ MISSING" errors
3. Test in frontend:
   - Safety zones should load on map
   - Cultural places should appear
   - SOS button should send SMS
   - Registration OTP should arrive in email

---

## 🚨 SendGrid Sender Verification

**IMPORTANT:** You must verify `kiranbhanu671@gmail.com` in SendGrid:

1. Go to: https://app.sendgrid.com/settings/sender_auth/senders
2. Click "Create New Sender" or "Verify Single Sender"
3. Enter kiranbhanu671@gmail.com
4. Check Gmail inbox for verification email
5. Click verification link
6. Wait for green checkmark

**Without this, NO emails will be sent!**

---

## 📝 Quick Copy-Paste (update YOUR values):

```bash
# Email
SENDGRID_API_KEY=SG.<YOUR_SENDGRID_API_KEY_HERE>
SENDGRID_FROM_EMAIL=kiranbhanu671@gmail.com

# AI Features
GEMINI_API_KEY=<GET_FROM_https://aistudio.google.com/app/apikey>

# SMS (Optional - set SMS_ENABLED=false if not using)
SMS_ENABLED=true
TWILIO_ACCOUNT_SID=<YOUR_SID>
TWILIO_AUTH_TOKEN=<YOUR_TOKEN>
TWILIO_PHONE_NUMBER=<YOUR_NUMBER>

# Frontend
FRONTEND_URL=https://thorough-reflection-production-1bb6.up.railway.app
```

---

## ⏱️ Timeline:

1. **Add variables to Railway** (2 minutes)
2. **Railway redeploys backend** (2-3 minutes)
3. **Verify SendGrid sender email** (5 minutes)
4. **Get Gemini API key** (2 minutes)
5. **Test all features** (5 minutes)

**Total: ~15 minutes**

---

## 🧪 Testing Checklist:

After setup, test these features:

- [ ] Tourist registration (OTP email)
- [ ] Safety zones appear on map (Gemini AI)
- [ ] Cultural places load (Gemini AI)
- [ ] SOS button works (SMS to emergency contact)
- [ ] Zone alerts trigger (entering caution/restricted zones)
- [ ] WebSocket connection works (no localhost:5000 errors)

