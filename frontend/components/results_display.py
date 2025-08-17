import streamlit as st
from typing import Dict, Any, List
from datetime import datetime

def render_results_display(deployment_result: Dict[str, Any]):
    
    if not deployment_result:
        st.warning("No deployment result to display")
        return
    
    st.subheader("🎯 Deployment Results")
    
    success = deployment_result.get("success", False)
    url = deployment_result.get("url")
    
    if success and url:
        _render_success_result(deployment_result)
    else:
        _render_error_result(deployment_result)

def _render_success_result(result: Dict[str, Any]):
    
    st.success("🎉 **Deployment Successful!**")
    
    url = result.get("url")
    provider = result.get("provider", "").upper()
    
    st.markdown(f"""
    ### 🌐 Your Website is Live!
    **URL:** [{url}]({url})
    
    Click the link above to view your deployed website.
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Open Website", type="primary", use_container_width=True):
            st.markdown(f'<script>window.open("{url}", "_blank")</script>', unsafe_allow_html=True)
    
    with col2:
        if st.button("📋 Copy URL", use_container_width=True):
            st.code(url)
    
    with col3:
        if st.button("📤 Share", use_container_width=True):
            _show_share_options(url)
    
    with st.expander("📊 Deployment Details", expanded=False):
        _render_deployment_details(result)
    
    _render_next_steps(result)

def _render_error_result(result: Dict[str, Any]):
    
    st.error("❌ **Deployment Failed**")
    
    error_msg = result.get("message", "Unknown error occurred")
    st.error(f"**Error:** {error_msg}")
    
    with st.expander("🔧 Troubleshooting", expanded=True):
        st.markdown("""
        **Common issues and solutions:**
        
        1. **Invalid Credentials**
           - Double-check your cloud provider credentials
           - Ensure proper permissions are set
        
        2. **Build Failures** 
           - Check if your repository has the correct build scripts
           - Verify package.json or requirements.txt
        
        3. **Network Issues**
           - Check your internet connection
           - Verify repository URL is accessible
        
        4. **Cloud Provider Issues**
           - Check service limits and quotas
           - Verify region availability
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Retry Deployment", type="primary"):
            st.info("Please try the deployment again from Step 3")
    
    with col2:
        if st.button("🏠 Start Over"):
            st.info("Starting over - please begin from Step 1")

def _render_deployment_details(result: Dict[str, Any]):
    
    provider = result.get("provider", "").upper()
    deployment_id = result.get("deployment_id", "N/A")
    deployed_at = result.get("deployed_at", "N/A")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("☁️ Provider", provider)
        st.metric("🆔 Deployment ID", deployment_id[:12] + "..." if len(deployment_id) > 12 else deployment_id)
    
    with col2:
        st.metric("📅 Deployed At", _format_datetime(deployed_at))
        st.metric("📁 Files Uploaded", result.get("uploaded_files", "N/A"))
    
    if provider == "AWS":
        _render_aws_details(result)
    elif provider == "AZURE":
        _render_azure_details(result)

def _render_aws_details(result: Dict[str, Any]):
    
    st.subheader("🟠 AWS Details")
    
    bucket_name = result.get("bucket_name", "N/A")
    region = result.get("region", "N/A")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**S3 Bucket:** {bucket_name}")
        st.write(f"**Region:** {region}")
    
    with col2:
        st.write("**Services Used:**")
        st.write("- Amazon S3 (Static Website Hosting)")
        st.write("- CloudFront (CDN) - Coming Soon")
    
    with st.expander("🔗 AWS Console Links"):
        console_base = f"https://console.aws.amazon.com"
        s3_url = f"{console_base}/s3/buckets/{bucket_name}?region={region}"
        
        st.markdown(f"- [S3 Bucket]({s3_url})")
        st.markdown(f"- [CloudFormation Stack](https://console.aws.amazon.com/cloudformation/)")

def _render_azure_details(result: Dict[str, Any]):
    
    st.subheader("🔵 Azure Details")
    
    storage_account = result.get("storage_account", "N/A")
    container_name = result.get("container_name", "$web")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Storage Account:** {storage_account}")
        st.write(f"**Container:** {container_name}")
    
    with col2:
        st.write("**Services Used:**")
        st.write("- Azure Blob Storage")
        st.write("- Static Website Hosting")
    
    with st.expander("🔗 Azure Portal Links"):
        portal_base = "https://portal.azure.com"
        storage_url = f"{portal_base}/#blade/Microsoft_Azure_Storage/BlobServiceMenuBlade/overview/storageAccountId/%2Fsubscriptions%2F<subscription>%2FresourceGroups%2F<rg>%2Fproviders%2FMicrosoft.Storage%2FstorageAccounts%2F{storage_account}"
        
        st.markdown(f"- [Storage Account]({portal_base})")
        st.markdown(f"- [Static Website Settings]({portal_base})")

def _render_next_steps(result: Dict[str, Any]):
    
    st.subheader("🚀 What's Next?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Immediate Actions:**
        - Test your website thoroughly
        - Share the URL with your team
        - Update your repository README with the live URL
        - Consider setting up monitoring
        """)
    
    with col2:
        st.markdown("""
        **🔧 Future Enhancements:**
        - Set up a custom domain
        - Configure CDN for better performance
        - Add SSL certificate (HTTPS)
        - Set up CI/CD for automatic deployments
        """)
    
    with st.expander("⚡ Performance Tips", expanded=False):
        st.markdown("""
        **To improve your website performance:**
        
        1. **Optimize Images**
           - Use WebP format when possible
           - Compress images before deployment
           - Consider using a CDN
        
        2. **Minimize Assets**
           - Minify CSS and JavaScript
           - Remove unused dependencies
           - Use tree shaking for smaller bundles
        
        3. **Caching Strategy**
           - Set appropriate cache headers
           - Use service workers for offline support
           - Implement browser caching
        
        4. **SEO Optimization**
           - Add meta tags
           - Create sitemap.xml
           - Optimize for search engines
        """)

def _show_share_options(url: str):
    
    st.subheader("📤 Share Your Website")
    
    twitter_url = f"https://twitter.com/intent/tweet?text=Check out my new website!&url={url}"
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={url}"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"[🐦 Twitter]({twitter_url})")
    
    with col2:
        st.markdown(f"[💼 LinkedIn]({linkedin_url})")
    
    with col3:
        st.markdown(f"[📧 Email](mailto:?subject=Check out my website&body=I just deployed a new website: {url})")
    
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        st.subheader("📱 QR Code")
        st.markdown(f'<img src="data:image/png;base64,{img_str}" width="200">', unsafe_allow_html=True)
        st.caption("Scan with your phone to open the website")
        
    except ImportError:
        st.info("Install qrcode library to generate QR codes: `pip install qrcode[pil]`")

def _format_datetime(datetime_str: str) -> str:
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime_str

def render_deployment_history(deployments: List[Dict[str, Any]]):
    if not deployments:
        st.info("No deployment history available")
        return
    
    st.subheader("📊 Recent Deployments")
    
    table_data = []
    for deployment in deployments:
        status = deployment.get("status", "unknown")
        status_emoji = {
            "completed": "✅",
            "failed": "❌", 
            "in_progress": "🔄"
        }.get(status, "❓")
        
        table_data.append({
            "ID": deployment.get("deployment_id", "N/A")[:12],
            "Provider": deployment.get("provider", "N/A").upper(),
            "Status": f"{status_emoji} {status}",
            "URL": deployment.get("url", "N/A"),
            "Deployed At": _format_datetime(deployment.get("deployed_at", "N/A"))
        })
    
    st.table(table_data)
