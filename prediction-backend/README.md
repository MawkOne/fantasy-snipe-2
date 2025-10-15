# Prediction Backend

Minimal FastAPI app exposing LMSR AMM endpoints backed by the shared Railway Postgres.

Run locally:

```bash
export DATABASE_URL="postgresql://..."
python3 -m uvicorn app:app --app-dir prediction-backend --host 0.0.0.0 --port 8100 --reload
```

Endpoints:
- GET /api/healthz
- POST /api/amm/markets
- GET /api/amm/markets/{market_id}
- POST /api/amm/markets/{market_id}/quote
- POST /api/amm/markets/{market_id}/trade


