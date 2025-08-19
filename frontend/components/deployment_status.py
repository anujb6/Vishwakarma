import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils.session_state import get_session_state, set_session_state, reset_deployment_state

def render_deployment_status(api_client):
    deployment_id = get_session_state("deployment_id")
    if not deployment_id:
        st.error("No deployment ID found")
        return
    
    st.subheader("🚀 Deployment Status")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.write(f"**Deployment ID:** `{deployment_id[:12]}...`")
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True, key="auto_refresh_chk")
    
    with col3:
        if st.button("🔍 Check Now", key="check_now_btn"):
            _check_deployment_status(api_client, deployment_id)
    
    with col4:
        if st.button("🔄 New Deployment", key="new_deployment_btn"):
            reset_deployment_state()
            set_session_state("current_step", 1)
            st.rerun()
    
    status_container = st.container()
    
    current_status = get_session_state("deployment_status", "unknown")
    
    if auto_refresh and current_status == "in_progress":
        time.sleep(10)
        st.rerun()
    
    _check_deployment_status(api_client, deployment_id, status_container)

def _check_deployment_status(api_client, deployment_id: str, container=None):    
    target = container if container is not None else st

    if container is not None:
        with container:
            _render_status(api_client, deployment_id, target)
    else:
        _render_status(api_client, deployment_id, target)


def _render_status(api_client, deployment_id, target):
    status_response = api_client.get_deployment_status(deployment_id)
    
    if not status_response:
        target.error("❌ Failed to get deployment status")
        return
    
    status = status_response.get("status", "unknown")
    url = status_response.get("url")
    logs = status_response.get("logs", [])
    created_at = status_response.get("created_at")
    completed_at = status_response.get("completed_at")
    
    set_session_state("deployment_status", status)
    set_session_state("deployment_url", url)
    set_session_state("last_status_check", datetime.now().isoformat())
    
    _display_status_info(status, url, created_at, completed_at)
    
    if logs:
        _display_deployment_logs(logs)
    
    if status == "completed" and url:
        _display_success_actions(url)
        set_session_state("step_deploy_done", True)
    elif status == "failed":
        _display_failure_actions()

def _display_status_info(status: str, url: Optional[str], created_at: Optional[str], completed_at: Optional[str]):
    if status == "completed":
        st.success("✅ **Deployment Completed Successfully!**")
    elif status == "failed":
        st.error("❌ **Deployment Failed**")
    elif status == "in_progress":
        st.info("🔄 **Deployment In Progress...**")
    else:
        st.warning(f"❓ **Status: {status.title()}**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if created_at:
            st.metric("📅 Started", _format_datetime(created_at))
    
    with col2:
        if completed_at:
            st.metric("⏱️ Completed", _format_datetime(completed_at))
        elif status == "in_progress":
            st.metric("⏱️ Duration", _calculate_duration(created_at))
    
    with col3:
        if url:
            st.metric("🌐 Status", "Live")
        else:
            st.metric("🌐 Status", "Deploying...")

def _display_deployment_logs(logs: list):
    st.subheader("📋 Deployment Logs")
    
    with st.expander("View Logs", expanded=False):
        log_container = st.container()
        
        with log_container:
            for log_entry in logs[-20:]:
                if isinstance(log_entry, dict):
                    timestamp = log_entry.get("timestamp", "")
                    message = log_entry.get("message", "")
                    
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%H:%M:%S")
                        except:
                            time_str = timestamp
                    else:
                        time_str = ""
                    
                    if "error" in message.lower() or "failed" in message.lower():
                        st.error(f"`{time_str}` {message}")
                    elif "success" in message.lower() or "completed" in message.lower():
                        st.success(f"`{time_str}` {message}")
                    elif "warning" in message.lower():
                        st.warning(f"`{time_str}` {message}")
                    else:
                        st.info(f"`{time_str}` {message}")
                else:
                    st.info(f"• {log_entry}")

def _display_success_actions(url: str):
    st.subheader("🎉 Deployment Successful!")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.success(f"🌐 **Your website is live at:** [{url}]({url})")
        
        st.info("""
        **What's next?**
        - Your website is now accessible worldwide
        - Changes to your repository will require a new deployment
        - Consider setting up a custom domain for production use
        """)
    
    with col2:
        st.write("**Quick Actions:**")
        
        if st.button("🌐 Open Website", use_container_width=True, key="open_website_btn"):
            st.markdown(f'<meta http-equiv="refresh" content="0; url={url}" />', unsafe_allow_html=True)
        
        if st.button("📋 Copy URL", use_container_width=True, key="copy_url_btn"):
            st.code(url)
            st.success("URL copied to display!")
        
        if st.button("📊 View Details", use_container_width=True, key="view_details_btn"):
            _show_deployment_details()

def _display_failure_actions():
    st.subheader("❌ Deployment Failed")
    
    st.error("""
    **Deployment failed!** Common issues:
    - Invalid credentials
    - Build process failed
    - Network connectivity issues
    - Insufficient permissions
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Retry Deployment", type="primary", key="retry_btn"):
            set_session_state("step_cloud_done", False)
            set_session_state("current_step", 2)
            reset_deployment_state()
            st.rerun()
    
    with col2:
        if st.button("🏠 Start Over", key="start_over_btn"):
            for key in list(st.session_state.keys()):
                if key.startswith(('repo_', 'analysis_', 'cloud_', 'deploy_')):
                    del st.session_state[key]
            set_session_state("current_step", 1)
            set_session_state("step_repo_done", False)
            set_session_state("step_cloud_done", False)
            set_session_state("step_deploy_done", False)
            st.rerun()

def _show_deployment_details():    
    with st.expander("📊 Deployment Details", expanded=True):
        st.subheader("📁 Repository")
        st.write(f"**URL:** {get_session_state('repo_url')}")
        st.write(f"**Branch:** {get_session_state('repo_branch')}")
        
        analysis = get_session_state("analysis_result", {}).get("analysis", {})
        if analysis:
            st.subheader("🔧 Build Configuration")
            st.write(f"**Framework:** {analysis.get('framework', 'Unknown')}")
            st.write(f"**Language:** {analysis.get('language', 'Unknown')}")
            if analysis.get("build_command"):
                st.write(f"**Build Command:** `{analysis.get('build_command')}`")
            st.write(f"**Output Directory:** {analysis.get('output_directory', 'build')}")
        
        cloud_config = get_session_state("cloud_config", {})
        if cloud_config:
            st.subheader("☁️ Cloud Configuration")
            st.write(f"**Provider:** {cloud_config.get('provider', 'Unknown').upper()}")
            if cloud_config.get("custom_domain"):
                st.write(f"**Custom Domain:** {cloud_config['custom_domain']}")

def _format_datetime(datetime_str: str) -> str:
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%m/%d %H:%M")
    except:
        return datetime_str

def _calculate_duration(start_time: str) -> str:
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        now = datetime.now()
        
        if start_dt.tzinfo and not now.tzinfo:
            import pytz
            now = pytz.UTC.localize(now)
        elif not start_dt.tzinfo and now.tzinfo:
            start_dt = start_dt.replace(tzinfo=now.tzinfo)
        
        duration = now - start_dt
        
        total_seconds = int(duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "Unknown"
