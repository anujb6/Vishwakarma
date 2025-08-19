import re
import logging
from typing import Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def validate_repo_url(repo_url: str) -> bool:
    try:
        parsed = urlparse(repo_url)
        
        if not parsed.scheme or not parsed.netloc:
            return False
        
        supported_hosts = [
            'github.com',
            'gitlab.com', 
            'bitbucket.org',
            'dev.azure.com',
            'git.sr.ht'
        ]
        
        host = parsed.netloc.lower()
        
        if host.startswith('www.'):
            host = host[4:]
        
        if not any(supported_host in host for supported_host in supported_hosts):
            logger.warning(f"Unsupported Git host: {host}")
            return False
        
        path_parts = [part for part in parsed.path.split('/') if part]
        if len(path_parts) < 2:
            return False
        
        repo_name = path_parts[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        if not re.match(r'^[a-zA-Z0-9._-]+$', repo_name):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating repo URL: {e}")
        return False

def validate_credentials(provider: str, credentials: Dict[str, str]) -> bool:
    if not credentials or not isinstance(credentials, dict):
        return False
    
    if provider == "aws":
        return validate_aws_credentials(credentials)
    elif provider == "azure":
        return validate_azure_credentials(credentials)
    else:
        logger.error(f"Unsupported provider: {provider}")
        return False

def validate_aws_credentials(credentials: Dict[str, str]) -> bool:
    required_fields = ['access_key_id', 'secret_access_key']
    
    for field in required_fields:
        if field not in credentials or not credentials[field].strip():
            logger.error(f"Missing or empty AWS credential: {field}")
            return False
    
    access_key = credentials['access_key_id'].strip()
    if not (access_key.startswith('AKIA') or access_key.startswith('ASIA')):
        logger.error("Invalid AWS access key format")
        return False
    
    if len(access_key) != 20:
        logger.error("Invalid AWS access key length")
        return False
    
    secret_key = credentials['secret_access_key'].strip()
    if len(secret_key) != 40:
        logger.error("Invalid AWS secret key length")
        return False
    
    if 'region' in credentials:
        region = credentials['region'].strip()
        if region and not re.match(r'^[a-z0-9-]+$', region):
            logger.error("Invalid AWS region format")
            return False
    
    return True

def validate_azure_credentials(credentials: Dict[str, str]) -> bool:
    if 'connection_string' in credentials:
        conn_str = credentials['connection_string'].strip()
        if not conn_str:
            return False
        
        required_parts = ['DefaultEndpointsProtocol', 'AccountName', 'AccountKey']
        return all(part in conn_str for part in required_parts)
    
    required_fields = ['tenant_id', 'client_id', 'client_secret', 'subscription_id']
    
    for field in required_fields:
        if field not in credentials or not credentials[field].strip():
            logger.error(f"Missing or empty Azure credential: {field}")
            return False
    
    guid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    for field in ['tenant_id', 'client_id', 'subscription_id']:
        if not re.match(guid_pattern, credentials[field].strip(), re.IGNORECASE):
            logger.error(f"Invalid Azure {field} format (should be GUID)")
            return False
    
    return True

def sanitize_project_name(name: str) -> str:
    if not name:
        return "project"
    
    sanitized = re.sub(r'[^a-zA-Z0-9-]', '-', name.lower())
    
    sanitized = sanitized.strip('-')
    
    if sanitized and sanitized[0].isdigit():
        sanitized = f"proj-{sanitized}"
    
    if len(sanitized) > 50:
        sanitized = sanitized[:50].rstrip('-')
    
    return sanitized or "project"

def validate_custom_domain(domain: str) -> bool:
    if not domain:
        return True
    
    domain = domain.strip().lower()
    
    if domain.startswith(('http://', 'https://')):
        domain = domain.split('://', 1)[1]
    
    domain = domain.rstrip('/')
    
    domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    
    return bool(re.match(domain_pattern, domain))