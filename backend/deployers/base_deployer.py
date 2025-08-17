from typing import Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseDeployer(ABC):
    
    def __init__(self):
        self.provider_name = ""
    
    @abstractmethod
    async def deploy(self, build_path: str, analysis: Dict[str, Any], 
                    credentials: Dict[str, str], custom_domain: str = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def delete_deployment(self, deployment_id: str) -> bool:
        pass