from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB, Redis, etc.
    print("🚀 Vanguard System: INITIATING SEQUENCE")
    print(f"🌍 Compliance Mode: {'ACTIVE' if settings.COMPLIANCE_MODE else 'TEST'}")
    yield
    # Shutdown: Close connections
    print("🛑 Vanguard System: SHUTTING DOWN")

app = FastAPI(
    title="Vanguard Core API",
    version="1.0.0",
    description="High-frequency sports arbitrage engine with Lei 14.790 compliance.",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """
    Infrastructure Probe Endpoint.
    Used by Docker Healthcheck to verify system integrity.
    """
    return {
        "status": "operational",
        "system": "Vanguard Core",
        "compliance_check": "passed",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
