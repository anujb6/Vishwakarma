import os
import json
import uuid
import mimetypes
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from backend.deployers.base_deployer import BaseDeployer
from backend.utils.excpetions import DeploymentError
from backend.utils.validation import sanitize_project_name

logger = logging.getLogger(__name__)

class AzureDeployer(BaseDeployer):    
    def __init__(self):
        super().__init__()
        self.provider_name = "azure"
        self.blob_client = None
        self.credentials = None
    
    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        if 'connection_string' in credentials:
            return bool(credentials['connection_string'].strip())
        
        required_fields = ['tenant_id', 'client_id', 'client_secret', 'subscription_id', 'storage_account']
        return all(field in credentials and credentials[field].strip() 
                  for field in required_fields)
    
    def _initialize_blob_client(self, credentials: Dict[str, str]):
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.identity import ClientSecretCredential
            
            if 'connection_string' in credentials:
                self.blob_client = BlobServiceClient.from_connection_string(
                    credentials['connection_string']
                )
            else:
                credential = ClientSecretCredential(
                    tenant_id=credentials['tenant_id'],
                    client_id=credentials['client_id'],
                    client_secret=credentials['client_secret']
                )
                
                storage_account = credentials['storage_account']
                account_url = f"https://{storage_account}.blob.core.windows.net"
                
                self.blob_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential
                )
            
            self.blob_client.get_account_information()
            logger.info("Successfully initialized Azure Blob Storage client")
            
        except Exception as e:
            raise DeploymentError(f"Failed to initialize Azure Blob Storage client: {str(e)}", "azure")
    
    async def deploy(self, build_path: str, analysis: Dict[str, Any], 
                    credentials: Dict[str, str], custom_domain: Optional[str] = None) -> Dict[str, Any]:
        try:
            if not self.validate_credentials(credentials):
                raise DeploymentError("Invalid Azure credentials provided", "azure")
            
            self._initialize_blob_client(credentials)
            
            deployment_id = str(uuid.uuid4())[:8]
            timestamp = int(datetime.now().timestamp())
            container_name = "$web"
            
            project_name = sanitize_project_name(analysis.get('framework', 'project'))
            storage_account = credentials.get('storage_account', f"deploy{deployment_id}")
            
            logger.info(f"Starting Azure deployment to storage account: {storage_account}")
            
            
            try:
                container_client = self.blob_client.get_container_client(container_name)
                container_client.get_container_properties()
            except Exception:
                logger.warning("$web container not found. Ensure static website hosting is enabled on the storage account.")
                raise DeploymentError("Static website hosting not enabled on storage account", "azure")
            
            uploaded_files = 0
            file_list = []
            
            for root, dirs, files in os.walk(build_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, build_path)
                    
                    blob_name = relative_path.replace(os.path.sep, '/')
                    
                    content_type, _ = mimetypes.guess_type(local_path)
                    if not content_type:
                        content_type = 'application/octet-stream'
                    
                    content_settings = {
                        'content_type': content_type
                    }
                    
                    if content_type.startswith(('text/', 'application/javascript', 'application/json')):
                        content_settings['cache_control'] = 'max-age=3600'
                    elif content_type.startswith(('image/', 'font/')):
                        content_settings['cache_control'] = 'max-age=86400'
                    
                    blob_client = self.blob_client.get_blob_client(
                        container=container_name, 
                        blob=blob_name
                    )
                    
                    with open(local_path, 'rb') as data:
                        blob_client.upload_blob(
                            data, 
                            overwrite=True,
                            content_settings=content_settings
                        )
                    
                    uploaded_files += 1
                    file_list.append(blob_name)
                    logger.debug(f"Uploaded: {blob_name}")
            
            deployment_metadata = {
                "deployment_id": deployment_id,
                "storage_account": storage_account,
                "container_name": container_name,
                "deployed_at": datetime.now().isoformat(),
                "uploaded_files": uploaded_files,
                "file_list": file_list,
                "custom_domain": custom_domain
            }
            
            metadata_blob = self.blob_client.get_blob_client(
                container=container_name,
                blob='.deployment-metadata.json'
            )
            
            metadata_blob.upload_blob(
                json.dumps(deployment_metadata),
                overwrite=True,
                content_settings={'content_type': 'application/json'}
            )
            
            if custom_domain:
                website_url = f"https://{custom_domain}"
            else:
                website_url = f"https://{storage_account}.z22.web.core.windows.net"
            
            logger.info(f"Azure deployment completed successfully. Uploaded {uploaded_files} files.")
            
            return {
                "success": True,
                "url": website_url,
                "provider": "azure",
                "storage_account": storage_account,
                "container_name": container_name,
                "uploaded_files": uploaded_files,
                "deployment_id": deployment_id,
                "deployed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Azure deployment failed: {e}")
            if isinstance(e, DeploymentError):
                raise
            raise DeploymentError(f"Azure deployment failed: {str(e)}", "azure")
    
    async def get_deployment_status(self, deployment_id: str, credentials: Dict[str, str] = None) -> Dict[str, Any]:
        try:
            if not credentials:
                return {"status": "unknown", "provider": "azure", "error": "Credentials required"}
            
            self._initialize_blob_client(credentials)
            
            container_name = "$web"
            
            try:
                metadata_blob = self.blob_client.get_blob_client(
                    container=container_name,
                    blob='.deployment-metadata.json'
                )
                
                blob_data = metadata_blob.download_blob()
                metadata = json.loads(blob_data.readall().decode('utf-8'))
                
                if metadata.get('deployment_id') == deployment_id:
                    return {
                        "status": "active",
                        "provider": "azure",
                        "deployment_id": deployment_id,
                        "metadata": metadata
                    }
                else:
                    return {"status": "not_found", "provider": "azure", "deployment_id": deployment_id}
                    
            except Exception:
                container_client = self.blob_client.get_container_client(container_name)
                blobs = list(container_client.list_blobs())
                
                if blobs:
                    return {
                        "status": "active",
                        "provider": "azure", 
                        "deployment_id": deployment_id,
                        "note": "Deployment exists but metadata not found"
                    }
                else:
                    return {"status": "not_found", "provider": "azure", "deployment_id": deployment_id}
                    
        except Exception as e:
            logger.error(f"Failed to get Azure deployment status: {e}")
            return {"status": "error", "provider": "azure", "error": str(e)}
    
    async def delete_deployment(self, deployment_id: str, credentials: Dict[str, str] = None) -> bool:
        try:
            if not credentials:
                logger.error("Credentials required for deployment deletion")
                return False
            
            self._initialize_blob_client(credentials)
            
            container_name = "$web"
            container_client = self.blob_client.get_container_client(container_name)
            
            try:
                metadata_blob = self.blob_client.get_blob_client(
                    container=container_name,
                    blob='.deployment-metadata.json'
                )
                
                blob_data = metadata_blob.download_blob()
                metadata = json.loads(blob_data.readall().decode('utf-8'))
                
                if metadata.get('deployment_id') != deployment_id:
                    logger.warning(f"Deployment ID mismatch. Expected: {deployment_id}, Found: {metadata.get('deployment_id')}")
                    return False
                
                file_list = metadata.get('file_list', [])
                file_list.append('.deployment-metadata.json')
                
                for blob_name in file_list:
                    try:
                        blob_client = self.blob_client.get_blob_client(
                            container=container_name,
                            blob=blob_name
                        )
                        blob_client.delete_blob()
                        logger.debug(f"Deleted blob: {blob_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete blob {blob_name}: {e}")
                
                logger.info(f"Successfully deleted Azure deployment: {deployment_id}")
                return True
                
            except Exception:
                logger.warning("No deployment metadata found. This operation will delete ALL files in the $web container.")
                
                blobs = container_client.list_blobs()
                for blob in blobs:
                    try:
                        blob_client = self.blob_client.get_blob_client(
                            container=container_name,
                            blob=blob.name
                        )
                        blob_client.delete_blob()
                    except Exception as e:
                        logger.warning(f"Failed to delete blob {blob.name}: {e}")
                
                logger.info("Deleted all blobs from $web container")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete Azure deployment: {e}")
            return False