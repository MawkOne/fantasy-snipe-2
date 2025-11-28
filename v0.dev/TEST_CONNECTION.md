# Test Cloud SQL Connection

## ✅ Setup Complete
- DATABASE_URL added to Railway
- 0.0.0.0/0 whitelisted in Cloud SQL

## Test 1: Health Check

```bash
curl https://fastapi-production-45ce.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Test 2: Query Database

```bash
curl https://fastapi-production-45ce.up.railway.app/api/test-query
```

**Expected Response:**
```json
{
  "database": "postgres",
  "user": "postgres",
  "version": "PostgreSQL 15.x ..."
}
```

## Test 3: Check What Tables Exist

```bash
curl https://fastapi-production-45ce.up.railway.app/api/tables
```

## If Tests Fail

1. **Check Railway Logs:**
   - Go to Railway → Your FastAPI project → "Deployments" tab
   - Look for errors

2. **Verify Environment Variable:**
   - Railway → Variables tab
   - Make sure DATABASE_URL is exactly:
     ```
     postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
     ```

3. **Redeploy:**
   - Railway → Click "Redeploy" (after adding env var)

## Next Steps After Connection Works

1. **Check what's in the database:**
   ```sql
   \dt  -- List all tables
   ```

2. **Import your JSON data** (if database is empty)

3. **Create API endpoints** for:
   - Leagues
   - Teams  
   - Transactions
   - Players
   - Weekly results

Let me know what you see when you test the connection!

