import os
from fastapi import FastAPI
from prediction_backend.routers.amm import router as amm_router
from prediction_backend.routers.forecasts import router as forecasts_router
from prediction_backend.config import PORT, HOST


app = FastAPI(title="Prediction Backend", version="0.1.0")


@app.get("/api/healthz")
def healthz():
    return {"ok": True}


app.include_router(amm_router)
app.include_router(forecasts_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=True)
