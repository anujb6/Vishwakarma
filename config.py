import os
from pathlib import Path
from typing import Any, Dict

class Config:
    CORS_ORIGINS = [
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ]
    
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    TEMP_DIR = BASE_DIR / "temp"
    LOGS_DIR = BASE_DIR / "logs"
    
    DATA_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    BUILD_TIMEOUT_SECONDS = int(os.getenv("BUILD_TIMEOUT_SECONDS", 600))
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 100))
    MAX_TOTAL_SIZE_MB = int(os.getenv("MAX_TOTAL_SIZE_MB", 500))
    
    CLONE_TIMEOUT_SECONDS = int(os.getenv("CLONE_TIMEOUT_SECONDS", 300))
    MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", 100))
    
    SUPPORTED_FRAMEWORKS = {
        "react": {
            "build_cmd": "npm run build",
            "output_dir": "build",
            "dev_dependencies": ["react", "react-dom"],
            "package_managers": ["npm", "yarn"]
        },
        "vue": {
            "build_cmd": "npm run build",
            "output_dir": "dist",
            "dev_dependencies": ["vue"],
            "package_managers": ["npm", "yarn"]
        },
        "angular": {
            "build_cmd": "npm run build",
            "output_dir": "dist",
            "dev_dependencies": ["@angular/core"],
            "package_managers": ["npm", "yarn"]
        },
        "next": {
            "build_cmd": "npm run build && npm run export",
            "output_dir": "out",
            "dev_dependencies": ["next"],
            "package_managers": ["npm", "yarn"]
        },
        "gatsby": {
            "build_cmd": "npm run build",
            "output_dir": "public",
            "dev_dependencies": ["gatsby"],
            "package_managers": ["npm", "yarn"]
        },
        "static": {
            "build_cmd": None,
            "output_dir": ".",
            "dev_dependencies": [],
            "package_managers": []
        },
        "vite": {
            "build_cmd": "npm run build",
            "output_dir": "dist",
            "dev_dependencies": ["vite"],
            "package_managers": ["npm", "yarn"]
        }
    }
    
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_WORKERS = int(os.getenv("API_WORKERS", 1))
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/deployments.db")
    
    AWS_MAX_BUCKET_SIZE_GB = int(os.getenv("AWS_MAX_BUCKET_SIZE_GB", 5))
    AZURE_MAX_STORAGE_SIZE_GB = int(os.getenv("AZURE_MAX_STORAGE_SIZE_GB", 5))
    
    MAX_CONCURRENT_DEPLOYMENTS = int(os.getenv("MAX_CONCURRENT_DEPLOYMENTS", 5))
    DEPLOYMENT_RETENTION_DAYS = int(os.getenv("DEPLOYMENT_RETENTION_DAYS", 30))
    
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = LOGS_DIR / "deployment.log"
    
    NODE_VERSION = os.getenv("NODE_VERSION", "16")
    PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.9")
    
    @classmethod
    def get_framework_config(cls, framework: str) -> Dict[str, Any]:
        return cls.SUPPORTED_FRAMEWORKS.get(framework, {})
    
    @classmethod
    def is_framework_supported(cls, framework: str) -> bool:
        return framework in cls.SUPPORTED_FRAMEWORKS
    
    @classmethod
    def get_all_supported_frameworks(cls) -> list:
        return list(cls.SUPPORTED_FRAMEWORKS.keys())

config = Config()