import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import config
from backend.services.build_service import BuildService
from backend.deployers.provider_factory import DeployerFactory

logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self):
        self.build_service = BuildService()
        self.deployer_factory = DeployerFactory()
        self.projects_dir = config.DATA_DIR / "projects"
        self.deployments_dir = config.DATA_DIR / "deployments"
        
        self.projects_dir.mkdir(exist_ok=True)
        self.deployments_dir.mkdir(exist_ok=True)
    
    def save_project(self, project_id: str, project_data: Dict[str, Any]):
        try:
            project_file = self.projects_dir / f"{project_id}.json"
            with open(project_file, 'w') as f:
                json.dump(project_data, f, indent=2)
            logger.info(f"Project {project_id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving project {project_id}: {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        try:
            project_file = self.projects_dir / f"{project_id}.json"
            if not project_file.exists():
                return None
            
            with open(project_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading project {project_id}: {e}")
            return None
    
    def save_deployment(self, deployment_id: str, deployment_data: Dict[str, Any]):
        try:
            deployment_file = self.deployments_dir / f"{deployment_id}.json"
            with open(deployment_file, 'w') as f:
                json.dump(deployment_data, f, indent=2)
            logger.info(f"Deployment {deployment_id} saved successfully")
        except Exception as e:
            logger.error(f"Error saving deployment {deployment_id}: {e}")
            raise
    
    def get_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        try:
            deployment_file = self.deployments_dir / f"{deployment_id}.json"
            if not deployment_file.exists():
                return None
            
            with open(deployment_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading deployment {deployment_id}: {e}")
            return None
    
    def update_deployment_status(self, deployment_id: str, status: str, 
                                data: Optional[Dict[str, Any]] = None):
        try:
            deployment_data = self.get_deployment(deployment_id) or {}
            deployment_data["status"] = status
            deployment_data["updated_at"] = datetime.now().isoformat()
            
            if data:
                deployment_data.update(data)
            
            if status in ["completed", "failed"]:
                deployment_data["completed_at"] = datetime.now().isoformat()
            
            self.save_deployment(deployment_id, deployment_data)
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")
    
    def add_deployment_log(self, deployment_id: str, log_message: str):
        try:
            deployment_data = self.get_deployment(deployment_id) or {}
            logs = deployment_data.get("logs", [])
            logs.append({
                "timestamp": datetime.now().isoformat(),
                "message": log_message
            })
            deployment_data["logs"] = logs
            self.save_deployment(deployment_id, deployment_data)
        except Exception as e:
            logger.error(f"Error adding deployment log: {e}")
    
    async def deploy_project(self, deployment_id: str, project_data: Dict[str, Any],
                           provider: str, credentials: Dict[str, str],
                           custom_domain: Optional[str] = None):
        try:
            deployment_data = {
                "id": deployment_id,
                "project_id": project_data["id"],
                "provider": provider,
                "status": "in_progress",
                "created_at": datetime.now().isoformat(),
                "logs": []
            }
            self.save_deployment(deployment_id, deployment_data)
            
            self.add_deployment_log(deployment_id, "Starting deployment process")
            
            self.add_deployment_log(deployment_id, "Building project...")
            build_output_path = await self.build_service.build_project(
                project_data["repo_path"],
                project_data["analysis"]
            )
            self.add_deployment_log(deployment_id, f"Build completed: {build_output_path}")
            
            self.add_deployment_log(deployment_id, f"Deploying to {provider}...")
            deployer = self.deployer_factory.get_deployer(provider)
            
            deployment_result = await deployer.deploy(
                build_output_path,
                project_data["analysis"],
                credentials,
                custom_domain
            )
            
            self.update_deployment_status(
                deployment_id,
                "completed",
                {
                    "url": deployment_result["url"],
                    "deployment_details": deployment_result
                }
            )
            
            self.add_deployment_log(deployment_id, f"Deployment completed successfully: {deployment_result['url']}")
            
        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            self.update_deployment_status(deployment_id, "failed", {"error": str(e)})
            self.add_deployment_log(deployment_id, f"Deployment failed: {str(e)}")
    
    def list_deployments(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            deployments = []
            deployment_files = list(self.deployments_dir.glob("*.json"))
            
            deployment_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for deployment_file in deployment_files[offset:offset+limit]:
                try:
                    with open(deployment_file, 'r') as f:
                        deployment_data = json.load(f)
                        deployment_summary = {
                            "id": deployment_data.get("id"),
                            "status": deployment_data.get("status"),
                            "provider": deployment_data.get("provider"),
                            "url": deployment_data.get("url"),
                            "created_at": deployment_data.get("created_at"),
                            "completed_at": deployment_data.get("completed_at")
                        }
                        deployments.append(deployment_summary)
                except Exception as e:
                    logger.error(f"Error reading deployment file {deployment_file}: {e}")
            
            return deployments
        except Exception as e:
            logger.error(f"Error listing deployments: {e}")
            return []