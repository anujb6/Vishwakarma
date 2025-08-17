from typing import Dict, Any
from abc import ABC, abstractmethod
import logging

from backend.deployers.aws_deployer import AWSDeployer
from backend.deployers.azure_deployer import AzureDeployer
from backend.deployers.base_deployer import BaseDeployer

logger = logging.getLogger(__name__)

class DeployerFactory:
    def __init__(self):
        self._deployers = {
            "aws": AWSDeployer,
            "azure": AzureDeployer
        }
    
    def get_deployer(self, provider: str) -> BaseDeployer:
        if provider not in self._deployers:
            raise ValueError(f"Unsupported provider: {provider}. Supported: {list(self._deployers.keys())}")
        
        return self._deployers[provider]()
    
    def get_supported_providers(self) -> list:
        return list(self._deployers.keys())
    
    def register_deployer(self, provider: str, deployer_class):
        if not issubclass(deployer_class, BaseDeployer):
            raise ValueError("Deployer class must inherit from BaseDeployer")
        
        self._deployers[provider] = deployer_class
        logger.info(f"Registered new deployer for provider: {provider}")
    
    def validate_provider_credentials(self, provider: str, credentials: Dict[str, str]) -> bool:
        if provider not in self._deployers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        deployer_instance = self._deployers[provider]()
        
        if hasattr(deployer_instance, 'validate_credentials'):
            return deployer_instance.validate_credentials(credentials)
        
        return bool(credentials)
    
    async def deploy_with_provider(self, provider: str, build_path: str, 
                                 analysis: Dict[str, Any], credentials: Dict[str, str], 
                                 custom_domain: str = None) -> Dict[str, Any]:
        try:
            deployer = self.get_deployer(provider)
            result = await deployer.deploy(build_path, analysis, credentials, custom_domain)
            
            if isinstance(result, dict):
                result["provider"] = provider
            
            return result
            
        except Exception as e:
            logger.error(f"Deployment failed for provider {provider}: {e}")
            raise
    
    async def get_deployment_status_with_provider(self, provider: str, deployment_id: str) -> Dict[str, Any]:
        try:
            deployer = self.get_deployer(provider)
            status = await deployer.get_deployment_status(deployment_id)
            
            if isinstance(status, dict):
                status["provider"] = provider
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get deployment status for provider {provider}: {e}")
            raise
    
    async def delete_deployment_with_provider(self, provider: str, deployment_id: str) -> bool:
        try:
            deployer = self.get_deployer(provider)
            return await deployer.delete_deployment(deployment_id)
            
        except Exception as e:
            logger.error(f"Failed to delete deployment for provider {provider}: {e}")
            raise


deployer_factory = DeployerFactory()