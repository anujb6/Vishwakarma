from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from pathlib import Path

from config import config
from backend.api.deploy import router as deploy_router
from backend.api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "backend.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Cloud Deployment Backend API",
    version=config.API_VERSION,
    description="Backend API for multi-cloud website deployment"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.include_router(health_router, prefix="/api")
app.include_router(deploy_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Multi-Cloud Deployment Backend API",
        "version": config.API_VERSION,
        "docs": "/docs"
    }