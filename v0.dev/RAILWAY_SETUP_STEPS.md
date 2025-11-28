# Railway Setup - FastAPI + Cloud SQL

## Step-by-Step Guide

### 1. Go to Your FastAPI Project on Railway

https://railway.app → Select your FastAPI project

### 2. Add Environment Variables

Click **"Variables"** tab and add:

```bash
DATABASE_URL=postgresql://postgres:123-new-password@34.47.23.137:5432/postgres?sslmode=require
```

That's it! Railway will automatically use `DATABASE_URL`.

### 3. Update Your FastAPI Code

```python
# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
def startup():
    models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Fantasy Hockey API", "status": "running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check database connection"""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/test-query")
def test_query(db: Session = Depends(get_db)):
    """Test a simple query"""
    try:
        result = db.execute("SELECT current_database(), current_user, version()")
        row = result.fetchone()
        return {
            "database": row[0],
            "user": row[1],
            "version": row[2]
        }
    except Exception as e:
        return {"error": str(e)}
```

### 4. Add `psycopg2` to `requirements.txt`

```txt
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
```

### 5. Whitelist Railway IP in Cloud SQL

1. Go to: https://console.cloud.google.com/sql/instances/nhl-api-db-montreal/connections/networking?project=fantasy-snipe-ai
2. Click **"Add Network"** under **Authorized Networks**
3. Name: `Railway`
4. Network: `0.0.0.0/0` (allows all IPs - for testing)
   - Or get Railway's specific outgoing IPs for production

### 6. Deploy

Push your code to GitHub, and Railway will auto-deploy!

### 7. Test Your API

```bash
# Health check
curl https://fastapi-production-45ce.up.railway.app/health

# Test query
curl https://fastapi-production-45ce.up.railway.app/api/test-query
```

## Common Issues

### Issue: "connection refused"
**Solution:** Check that Cloud SQL allows Railway's IP

### Issue: "password authentication failed"
**Solution:** Double-check the password in Railway env vars

### Issue: "SSL required"
**Solution:** Make sure `?sslmode=require` is in the connection string

### Issue: "database does not exist"
**Solution:** The database name is `postgres` (default) - create your own database if needed:

```sql
CREATE DATABASE nhl_api;
```

Then update connection string:
```
postgresql://postgres:123-new-password@34.47.23.137:5432/nhl_api?sslmode=require
```

## Next Steps

1. ✅ Connection string configured
2. 🔲 Add environment variable to Railway
3. 🔲 Whitelist Railway IP in Cloud SQL
4. 🔲 Update FastAPI code
5. 🔲 Deploy and test `/health` endpoint
6. 🔲 Create database schema
7. 🔲 Import historical data
8. 🔲 Build API endpoints

