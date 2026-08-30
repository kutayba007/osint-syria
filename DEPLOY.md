# 🇸🇾 OSINT Syria — Deployment Guide

## Quick Deploy to Render (Backend API)

### Step 1: Push to GitHub
```bash
cd osint-syria
git init
git add .
git commit -m "Initial OSINT Syria deployment"
git remote add origin https://github.com/YOUR_USERNAME/osint-syria.git
git push -u origin main
```

### Step 2: Deploy to Render
1. Go to https://dashboard.render.com
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Settings:
   - **Name**: `osint-syria-api`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (from .env)
6. Click **Create Web Service**

### Step 3: Get Your API URL
After deployment, Render gives you a URL like:
```
https://osint-syria-api.onrender.com
```

Test it:
```
https://osint-syria-api.onrender.com/api/health
```

---

## Quick Deploy to Streamlit Cloud (Dashboard)

### Step 1: Deploy Dashboard
1. Go to https://share.streamlit.io
2. Click **New app**
3. Select your repo
4. Set path: `dashboard/app.py`
5. Click **Deploy!**

### Step 2: Get Your Dashboard URL
Streamlit gives you a URL like:
```
https://osint-syria-dashboard.streamlit.app
```

---

## Environment Variables for Render

Set these in Render Dashboard → Environment:

```
TG_API_ID=34020466
TG_API_HASH=5ce4f1fddca194a56718f2b4c15e1ba6
TG_PHONE_NUMBER=+905380848357
TG_BOT_TOKEN=8842860890:AAEwh2OAua1s4fqWJGUqLC0UGuYzVMBk7iw
TG_ALERT_CHAT_ID=1941197054
GROQ_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
```

---

## Cost Summary

| Service | Plan | Cost |
|---------|------|------|
| Render (API) | Free | $0 |
| Streamlit Cloud | Free | $0 |
| Telegram API | Free | $0 |
| Groq AI | Free | $0 |
| Supabase | Free | $0 |
| **Total** | | **$0** |
