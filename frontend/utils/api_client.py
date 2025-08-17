import requests
import streamlit as st
from typing import Dict, Any, Optional
import logging
import os
logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000/api")
        self.timeout = 30
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            st.error(f"API Error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            st.error(f"Unexpected error: {str(e)}")
            return None
    
    def analyze_repository(self, repo_url: str, branch: str = "main") -> Optional[Dict[str, Any]]:
        data = {
            "repo_url": repo_url,
            "branch": branch
        }
        
        return self._make_request("POST", "/analyze", json=data)
    
    def deploy_project(self, deploy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._make_request("POST", "/deploy", json=deploy_data)
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        return self._make_request("GET", f"/status/{deployment_id}")
    
    def get_recent_deployments(self, limit: int = 10) -> Optional[Dict[str, Any]]:
        params = {"limit": limit}
        return self._make_request("GET", "/deployments", params=params)
    
    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False