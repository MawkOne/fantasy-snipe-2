# Quick Start - Connect Everything

## Your Infrastructure

```
┌─────────────────────┐
│   Next.js Frontend  │  (localhost:3000 / Vercel)
│   /v0.dev           │
└──────────┬──────────┘
           │
           ├──────────▶ Firebase (Chat, Auth)
           │            snipe-chat-139ec.firebaseapp.com
           │
           └──────────▶ FastAPI (API)
                        fastapi-production-45ce.up.railway.app
                        │
                        └──────────▶ Google Cloud SQL (Data)
                                    34.47.23.137:5432
```

## 1. Firebase (✅ Already Connected)

Your chat is working with Firebase!

**Config:** Already in `.env.local`

## 2. Google Cloud SQL (✅ Connection String Ready)

**Connection String:**
```
postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
```

**What's Inside?**
- Historical fantasy hockey data
- League history, transactions, rosters
- Player stats, weekly results

## 3. FastAPI Backend (⏳ Needs Setup)

**URL:** https://fastapi-production-45ce.up.railway.app

**To Do:**
1. Add environment variable to Railway:
   ```
   DATABASE_URL=postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
   ```

2. Whitelist Railway IP in Cloud SQL Console:
   https://console.cloud.google.com/sql/instances/nhl-api-db-montreal/connections/networking?project=fantasy-snipe-ai

3. Update FastAPI code (see `RAILWAY_SETUP_STEPS.md`)

4. Deploy and test:
   ```bash
   curl https://fastapi-production-45ce.up.railway.app/health
   ```

## 4. Next.js Frontend (✅ Running)

**Port:** 3000  
**Dark Mode:** ✅ Discord theme  
**Real-time Chat:** ✅ Firebase  
**League Switching:** ✅ Ready (needs data)

## What Works Right Now

✅ Chat messaging (Firebase)  
✅ Dark mode theme  
✅ League sidebar (ready for real data)  
✅ Discord-style compact UI  

## What Needs Data

🔲 League list (will come from Cloud SQL)  
🔲 Team rosters (Cloud SQL)  
🔲 Transaction history (Cloud SQL)  
🔲 Player stats (Cloud SQL)  
🔲 Analytics (Cloud SQL)  

## Next Actions

### Option A: Connect FastAPI to Cloud SQL
1. Follow `RAILWAY_SETUP_STEPS.md`
2. Deploy endpoints
3. Test from frontend

### Option B: Import JSON Data
1. Run import script (I can create this)
2. Load `uhhp_league_history_full.json` into Cloud SQL
3. Connect via FastAPI

### Option C: Use PostgreSQL on Railway
1. Use your existing Railway DB:
   ```
   postgresql://postgres:WbUPvsoAtcwLhxCDMPOygaFHuALRTcWa@shuttle.proxy.rlwy.net:34371/railway
   ```
2. Import data there instead
3. Skip Cloud SQL

## Test Your Stack

```bash
# 1. Test Firebase (should work)
# Open http://localhost:3000 and send a message

# 2. Test Cloud SQL (from local machine)
psql "postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require"

# 3. Test FastAPI (once deployed)
curl https://fastapi-production-45ce.up.railway.app/health
```

## Questions?

- Want me to create the FastAPI endpoints?
- Should I import the JSON data?
- Prefer Railway PostgreSQL instead of Cloud SQL?
- Need help with any setup step?

Everything is ready to connect! 🚀

