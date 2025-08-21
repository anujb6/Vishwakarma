import streamlit as st
import re
from typing import Dict, Any, Optional
from utils.session_state import set_session_state
import re
import boto3
from botocore.exceptions import ClientError

def render_cloud_selector() -> Optional[Dict[str, Any]]:    
    st.subheader("☁️ Choose Your Cloud Provider")
    
    # Provider selection
    provider = st.selectbox(
        "Select Cloud Provider",
        options=["aws", "azure"],
        format_func=lambda x: {
            "aws": "🟠 Amazon Web Services (AWS)",
            "azure": "🔵 Microsoft Azure"
        }[x],
        help="Choose the cloud provider where you want to deploy your application"
    )
    
    set_session_state("selected_provider", provider)
    
    if provider == "aws":
        credentials = _render_aws_config()
    elif provider == "azure":
        credentials = _render_azure_config()
    else:
        st.error("Unsupported provider selected")
        return None
    
    st.subheader("🌐 Custom Domain (Optional)")
    custom_domain = st.text_input(
        "Custom Domain",
        placeholder="example.com",
        help="Optional: Enter your custom domain name"
    )
    
    if custom_domain:
        if not _validate_domain(custom_domain):
            st.warning("⚠️ Please enter a valid domain name (e.g., example.com)")
        else:
            st.success("✅ Valid domain format")
    
    if credentials:
        st.subheader("📋 Configuration Summary")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**Provider:** {provider.upper()}")
            if custom_domain:
                st.info(f"**Custom Domain:** {custom_domain}")
            
            if provider == "aws":
                st.info("**Service:** S3 + CloudFront")
                st.info("**Features:** Static website hosting, CDN, HTTPS")
            elif provider == "azure":
                st.info("**Service:** Blob Storage Static Websites")
                st.info("**Features:** Static website hosting, CDN-ready")
        
        with col2:
            st.write("")
            if st.button("✅ Confirm Configuration", type="primary", use_container_width=True):
                return {
                    "provider": provider,
                    "credentials": credentials,
                    "custom_domain": custom_domain if custom_domain and _validate_domain(custom_domain) else None
                }
    
    return None

def _render_aws_config() -> Optional[Dict[str, str]]:
    
    st.subheader("🟠 AWS Configuration")
    
    with st.expander("ℹ️ How to get AWS credentials", expanded=False):
        st.markdown("""
        **To get your AWS credentials:**
        1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
        2. Create a new user or select existing user
        3. Attach policy: `AmazonS3FullAccess`
        4. Generate Access Key ID and Secret Access Key
        5. Copy the credentials below
        
        **Required Permissions:**
        - `s3:CreateBucket`
        - `s3:PutObject`
        - `s3:PutBucketWebsite`
        - `s3:PutBucketPolicy`
        """)
    
    access_key_id = st.text_input(
        "Access Key ID",
        type="password",
        placeholder="AKIA...",
        help="Your AWS Access Key ID"
    )
    
    secret_access_key = st.text_input(
        "Secret Access Key",
        type="password",
        placeholder="Enter your secret key",
        help="Your AWS Secret Access Key"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        region = st.selectbox(
            "AWS Region",
            options=[
                "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
                "ap-southeast-1", "ap-northeast-1", "ap-south-1"
            ],
            index=0,
            help="AWS region for deployment"
        )
    
    with col2:
        session_token = st.text_input(
            "Session Token (Optional)",
            type="password",
            help="Only needed for temporary credentials"
        )
    
    if access_key_id and secret_access_key:
        if _validate_aws_credentials(access_key_id, secret_access_key):
            st.success("✅ AWS credentials format looks good!")
            return {
                "access_key_id": access_key_id,
                "secret_access_key": secret_access_key,
                "region": region,
                "session_token": session_token if session_token else None
            }
        else:
            st.error("❌ Invalid AWS credentials format")
    
    return None

def _render_azure_config() -> Optional[Dict[str, str]]:
    
    st.subheader("🔵 Azure Configuration")
    
    with st.expander("ℹ️ How to get Azure credentials", expanded=False):
        st.markdown("""
        **To get your Azure credentials:**
        1. Go to [Azure Portal](https://portal.azure.com/)
        2. Navigate to **Azure Active Directory** > **App registrations**
        3. Create a new application registration
        4. Go to **Certificates & secrets** and create a new client secret
        5. Note down the **Application (client) ID**, **Directory (tenant) ID**, and **Client secret**
        6. Assign **Storage Blob Data Contributor** role to your app
        
        **Required Permissions:**
        - `Microsoft.Storage/storageAccounts/write`
        - `Microsoft.Storage/storageAccounts/blobServices/containers/write`
        - `Microsoft.Storage/storageAccounts/blobServices/generateUserDelegationKey/action`
        """)
    
    auth_method = st.radio(
        "Authentication Method",
        options=["service_principal", "connection_string"],
        format_func=lambda x: {
            "service_principal": "🔐 Service Principal (Recommended)",
            "connection_string": "🔗 Connection String"
        }[x],
        help="Choose how to authenticate with Azure"
    )
    
    if auth_method == "service_principal":
        tenant_id = st.text_input(
            "Tenant ID",
            type="password",
            placeholder="12345678-1234-1234-1234-123456789abc",
            help="Your Azure AD Tenant ID"
        )
        
        client_id = st.text_input(
            "Client ID",
            type="password",
            placeholder="12345678-1234-1234-1234-123456789abc",
            help="Your Azure AD Application (Client) ID"
        )
        
        client_secret = st.text_input(
            "Client Secret",
            type="password",
            placeholder="Enter your client secret",
            help="Your Azure AD Application Client Secret"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            subscription_id = st.text_input(
                "Subscription ID",
                placeholder="12345678-1234-1234-1234-123456789abc",
                help="Your Azure Subscription ID"
            )
        
        with col2:
            resource_group = st.text_input(
                "Resource Group",
                placeholder="my-resource-group",
                help="Resource group for the storage account"
            )
        
        if all([tenant_id, client_id, client_secret, subscription_id, resource_group]):
            if _validate_azure_service_principal(tenant_id, client_id, client_secret, subscription_id):
                st.success("✅ Azure service principal credentials format looks good!")
                return {
                    "auth_method": "service_principal",
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "subscription_id": subscription_id,
                    "resource_group": resource_group
                }
            else:
                st.error("❌ Invalid Azure service principal credentials format")
    
    else:
        st.warning("⚠️ Connection strings provide full access to your storage account. Use with caution.")
        
        connection_string = st.text_area(
            "Connection String",
            placeholder="DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net",
            help="Your Azure Storage Account connection string",
            height=100
        )
        
        if connection_string:
            if _validate_azure_connection_string(connection_string):
                st.success("✅ Azure connection string format looks good!")
                return {
                    "auth_method": "connection_string",
                    "connection_string": connection_string
                }
            else:
                st.error("❌ Invalid Azure connection string format")
    
    return None

def _validate_domain(domain: str) -> bool:
    if not domain:
        return False
    
    domain = domain.replace("http://", "").replace("https://", "")
    
    domain = domain.rstrip("/")
    
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(domain_pattern, domain):
        return False
    
    if len(domain) > 255:
        return False
    
    parts = domain.split('.')
    if len(parts) < 2 or len(parts[-1]) < 2:
        return False
    
    if '..' in domain:
        return False
    
    for part in parts:
        if not part or part.startswith('-') or part.endswith('-'):
            return False
    
    return True

def _validate_aws_credentials(access_key_id: str, secret_access_key: str) -> bool:
    access_key_pattern = r'^(AKIA|ASIA|AGPA|AIDA|ANPA|AROA)[A-Z0-9]{16}$'
    secret_key_pattern = r'^[A-Za-z0-9/+=]{40}$'

    if not (re.match(access_key_pattern, access_key_id) and re.match(secret_key_pattern, secret_access_key)):
        return False

    try:
        boto3.client(
            "sts",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        ).get_caller_identity()
        return True
    except ClientError:
        return False

def _validate_azure_service_principal(tenant_id: str, client_id: str, client_secret: str, subscription_id: str) -> bool:
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    if not all(re.match(uuid_pattern, id_.lower()) for id_ in [tenant_id, client_id, subscription_id]):
        return False
    
    if not client_secret or len(client_secret) < 8:
        return False
    
    return True

def _validate_azure_connection_string(connection_string: str) -> bool:
    required_parts = [
        'DefaultEndpointsProtocol=',
        'AccountName=',
        'AccountKey=',
        'EndpointSuffix='
    ]
    
    for part in required_parts:
        if part not in connection_string:
            return False
    
    if len(connection_string) < 100:
        return False
    
    return True