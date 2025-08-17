import json
import os
import mimetypes
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from backend.deployers.base_deployer import BaseDeployer

logger = logging.getLogger(__name__)

class AWSDeployer(BaseDeployer):
    def __init__(self):
        super().__init__()
        self.provider_name = "aws"
    
    def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        required_fields = ['access_key_id', 'secret_access_key']
        return all(field in credentials and credentials[field].strip() 
                  for field in required_fields)
    
    async def deploy(self, build_path: str, analysis: Dict[str, Any], 
                    credentials: Dict[str, str], custom_domain: Optional[str] = None) -> Dict[str, Any]:
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            if not self.validate_credentials(credentials):
                raise ValueError("Invalid AWS credentials provided")
            
            deployment_id = str(uuid.uuid4())[:8]
            timestamp = int(datetime.now().timestamp())
            bucket_name = f"deploy-{deployment_id}-{timestamp}"
            
            logger.info(f"Starting AWS deployment to bucket: {bucket_name}")
            
            session = boto3.Session(
                aws_access_key_id=credentials["access_key_id"],
                aws_secret_access_key=credentials["secret_access_key"],
                aws_session_token=credentials.get("session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            
            s3_client = session.client('s3')
            region = credentials.get("region", "us-east-1")
            
            try:
                if region != "us-east-1":
                    s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )
                else:
                    s3_client.create_bucket(Bucket=bucket_name)
                    
                logger.info(f"Created S3 bucket: {bucket_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'BucketAlreadyExists':
                    timestamp = int(datetime.now().timestamp())
                    bucket_name = f"deploy-{deployment_id}-{timestamp}"
                    if region != "us-east-1":
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    else:
                        s3_client.create_bucket(Bucket=bucket_name)
                else:
                    raise
            
            s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'},
                    'ErrorDocument': {'Key': 'error.html'}
                }
            )
            
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }]
            }
            
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            uploaded_files = 0
            for root, dirs, files in os.walk(build_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, build_path)
                    
                    s3_key = relative_path.replace(os.path.sep, '/')
                    
                    content_type, _ = mimetypes.guess_type(local_path)
                    if not content_type:
                        content_type = 'binary/octet-stream'
                    
                    extra_args = {'ContentType': content_type}
                    if content_type.startswith(('text/', 'application/javascript', 'application/json')):
                        extra_args['CacheControl'] = 'max-age=3600' 
                    elif content_type.startswith(('image/', 'font/')):
                        extra_args['CacheControl'] = 'max-age=86400'
                    
                    s3_client.upload_file(
                        local_path,
                        bucket_name,
                        s3_key,
                        ExtraArgs=extra_args
                    )
                    uploaded_files += 1
                    logger.debug(f"Uploaded: {s3_key}")
            
            if region == "us-east-1":
                website_url = f"https://{bucket_name}.s3-website-us-east-1.amazonaws.com"
            else:
                website_url = f"https://{bucket_name}.s3-website.{region}.amazonaws.com"
            
            deployment_metadata = {
                "deployment_id": deployment_id,
                "bucket_name": bucket_name,
                "region": region,
                "deployed_at": datetime.now().isoformat(),
                "uploaded_files": uploaded_files,
                "custom_domain": custom_domain
            }
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key='.deployment-metadata.json',
                Body=json.dumps(deployment_metadata),
                ContentType='application/json'
            )
            
            logger.info(f"AWS deployment completed successfully. Uploaded {uploaded_files} files.")
            
            return {
                "success": True,
                "url": website_url,
                "provider": "aws",
                "bucket_name": bucket_name,
                "region": region,
                "uploaded_files": uploaded_files,
                "deployment_id": deployment_id,
                "deployed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AWS deployment failed: {e}")
            raise Exception(f"AWS deployment failed: {str(e)}")
    
    async def get_deployment_status(self, deployment_id: str, credentials: Dict[str, str] = None) -> Dict[str, Any]:
        try:
            if not credentials:
                return {"status": "unknown", "provider": "aws", "error": "Credentials required"}
            
            import boto3
            from botocore.exceptions import ClientError
            
            session = boto3.Session(
                aws_access_key_id=credentials["access_key_id"],
                aws_secret_access_key=credentials["secret_access_key"],
                aws_session_token=credentials.get("session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            
            s3_client = session.client('s3')
            
            buckets = s3_client.list_buckets()
            deployment_bucket = None
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                if deployment_id in bucket_name:
                    try:
                        s3_client.head_object(Bucket=bucket_name, Key='.deployment-metadata.json')
                        deployment_bucket = bucket_name
                        break
                    except ClientError:
                        continue
            
            if not deployment_bucket:
                return {"status": "not_found", "provider": "aws", "deployment_id": deployment_id}
            
            try:
                response = s3_client.get_object(Bucket=deployment_bucket, Key='.deployment-metadata.json')
                metadata = json.loads(response['Body'].read().decode('utf-8'))
                
                return {
                    "status": "active",
                    "provider": "aws",
                    "deployment_id": deployment_id,
                    "bucket_name": deployment_bucket,
                    "metadata": metadata
                }
            except ClientError:
                return {
                    "status": "active", 
                    "provider": "aws", 
                    "deployment_id": deployment_id,
                    "bucket_name": deployment_bucket
                }
                
        except Exception as e:
            logger.error(f"Failed to get AWS deployment status: {e}")
            return {"status": "error", "provider": "aws", "error": str(e)}
    
    async def delete_deployment(self, deployment_id: str, credentials: Dict[str, str] = None) -> bool:
        try:
            if not credentials:
                logger.error("Credentials required for deployment deletion")
                return False
            
            import boto3
            from botocore.exceptions import ClientError
            
            session = boto3.Session(
                aws_access_key_id=credentials["access_key_id"],
                aws_secret_access_key=credentials["secret_access_key"],
                aws_session_token=credentials.get("session_token"),
                region_name=credentials.get("region", "us-east-1")
            )
            
            s3_client = session.client('s3')
            
            buckets = s3_client.list_buckets()
            deployment_bucket = None
            
            for bucket in buckets['Buckets']:
                bucket_name = bucket['Name']
                if deployment_id in bucket_name:
                    deployment_bucket = bucket_name
                    break
            
            if not deployment_bucket:
                logger.warning(f"No bucket found for deployment_id: {deployment_id}")
                return False
            
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=deployment_bucket)
            
            for page in pages:
                if 'Contents' in page:
                    objects = [{'Key': obj['Key']} for obj in page['Contents']]
                    s3_client.delete_objects(
                        Bucket=deployment_bucket,
                        Delete={'Objects': objects}
                    )
            
            s3_client.delete_bucket(Bucket=deployment_bucket)
            
            logger.info(f"Successfully deleted AWS deployment: {deployment_bucket}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete AWS deployment: {e}")
            return False