import uvicorn
from config import config

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )