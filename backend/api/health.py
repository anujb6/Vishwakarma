from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": datetime.now().timestamp(),
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "disk_usage": f"{psutil.disk_usage('/').percent}%"
    }