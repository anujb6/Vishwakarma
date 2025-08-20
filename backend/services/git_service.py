import git
import os
import hashlib
import shutil
from pathlib import Path
import logging
from typing import Optional

from config import config

logger = logging.getLogger(__name__)

class GitService:
    def __init__(self):
        self.temp_dir = config.TEMP_DIR / "repos"
        self.temp_dir.mkdir(exist_ok=True)
    
    def _get_repo_hash(self, repo_url: str, branch: str = "main") -> str:
        combined = f"{repo_url}#{branch}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    async def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        try:
            repo_hash = self._get_repo_hash(repo_url, branch)
            repo_path = self.temp_dir / repo_hash
            
            if repo_path.exists():
                shutil.rmtree(repo_path)
            
            logger.info(f"Cloning repository {repo_url} branch {branch} to {repo_path}")
            
            repo = git.Repo.clone_from(
                repo_url, 
                repo_path
            )
            
            logger.info(f"Successfully cloned repository to {repo_path}")
            return str(repo_path)
            
        except git.exc.GitCommandError as e:
            logger.error(f"Git clone error: {e}")
            raise Exception(f"Failed to clone repository: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error cloning repository: {e}")
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def get_branches(self, repo_path: str) -> list:
        try:
            repo = git.Repo(repo_path)
            branches = [str(branch).replace('origin/', '') for branch in repo.remote().refs]
            return branches
        except Exception as e:
            logger.error(f"Error getting branches: {e}")
            return ["main"]
    
    def cleanup_repo(self, repo_path: str):
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository at {repo_path}")
        except Exception as e:
            logger.error(f"Error cleaning up repository: {e}")