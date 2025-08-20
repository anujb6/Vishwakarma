#frontend/app.py
import streamlit as st
from typing import Dict, Any, Optional

from components.cloud_selector import render_cloud_selector
from components.repo_analyzer import render_repo_analyzer
from components.deployment_status import render_deployment_status
from components.results_display import render_results_display
from utils.api_client import APIClient
from utils.session_state import init_session_state, get_session_state, set_session_state

st.set_page_config(
    page_title="Multi-Cloud Deployer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .step-container {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    
    .step-active {
        border-color: #667eea;
        background-color: #f0f4ff;
    }
    
    .step-completed {
        border-color: #28a745;
        background-color: #f0fff4;
    }
    
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    
    .deployment-card {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    init_session_state()
    
    api_client = APIClient()
    
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Multi-Cloud Website Deployer</h1>
        <p>Deploy your frontend applications to AWS & Azure with ease</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("🎯 Deployment Steps")
        
        steps = [
            ("1️⃣", "Repository Analysis", get_session_state("step_repo_done")),
            ("2️⃣", "Cloud Provider", get_session_state("step_cloud_done")),
            ("3️⃣", "Deployment", get_session_state("step_deploy_done"))
        ]
        
        for icon, step_name, completed in steps:
            if completed:
                st.success(f"{icon} {step_name} ✅")
            else:
                st.info(f"{icon} {step_name}")
        
        st.divider()
        
        if st.button("🔄 Reset All", help="Start over with a new deployment"):
            for key in list(st.session_state.keys()):
                if key.startswith(('repo_', 'analysis_', 'cloud_', 'deploy_')):
                    del st.session_state[key]
            set_session_state("current_step", 1)
            set_session_state("step_repo_done", False)
            set_session_state("step_cloud_done", False)
            set_session_state("step_deploy_done", False)
            st.rerun()
        
        if get_session_state("deployment_id"):
            st.divider()
            st.subheader("🔄 Current Deployment")
            st.write(f"**ID:** {get_session_state('deployment_id')[:8]}...")
            st.write(f"**Provider:** {get_session_state('selected_provider', 'Unknown')}")
            
            if st.button("📊 Check Status"):
                st.rerun()
    
    current_step = get_session_state("current_step", 1)
    
    if current_step >= 1:
        step_class = "step-active" if current_step == 1 else ("step-completed" if get_session_state("step_repo_done") else "step-container")
        st.markdown(f'<div class="{step_class}">', unsafe_allow_html=True)
        
        st.header("1️⃣ Repository Analysis")
        
        if not get_session_state("step_repo_done"):
            analysis_result = render_repo_analyzer(api_client)
            if analysis_result:
                set_session_state("analysis_result", analysis_result)
                set_session_state("step_repo_done", True)
                set_session_state("current_step", 2)
                st.rerun()
        else:
            analysis = get_session_state("analysis_result")
            if analysis:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("✅ Repository analyzed successfully!")
                    st.write(f"**Repository:** {get_session_state('repo_url')}")
                    st.write(f"**Framework:** {analysis['analysis'].get('framework', 'Unknown')}")
                    st.write(f"**Language:** {analysis['analysis'].get('language', 'Unknown')}")
                
                with col2:
                    if st.button("🔄 Re-analyze Repository"):
                        set_session_state("step_repo_done", False)
                        set_session_state("current_step", 1)
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if current_step >= 2 and get_session_state("step_repo_done"):
        step_class = "step-active" if current_step == 2 else ("step-completed" if get_session_state("step_cloud_done") else "step-container")
        st.markdown(f'<div class="{step_class}">', unsafe_allow_html=True)
        
        st.header("2️⃣ Cloud Provider Selection")
        
        if not get_session_state("step_cloud_done"):
            cloud_config = render_cloud_selector()
            if cloud_config:
                set_session_state("cloud_config", cloud_config)
                set_session_state("step_cloud_done", True)
                set_session_state("current_step", 3)
                st.rerun()
        else:
            cloud_config = get_session_state("cloud_config")
            if cloud_config:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("✅ Cloud provider configured!")
                    st.write(f"**Provider:** {cloud_config.get('provider', 'Unknown').upper()}")
                    if cloud_config.get('custom_domain'):
                        st.write(f"**Custom Domain:** {cloud_config['custom_domain']}")
                
                with col2:
                    if st.button("🔄 Change Provider"):
                        set_session_state("step_cloud_done", False)
                        set_session_state("current_step", 2)
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if current_step >= 3 and get_session_state("step_repo_done") and get_session_state("step_cloud_done"):
        st.markdown('<div class="step-active">', unsafe_allow_html=True)
        
        st.header("3️⃣ Deploy Your Application")
        
        if not get_session_state("deployment_id"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info("Ready to deploy! Click the button to start the deployment process.")
                analysis = get_session_state("analysis_result")
                cloud_config = get_session_state("cloud_config")
                
                with st.expander("📋 Deployment Summary", expanded=True):
                    st.write("**Repository Information:**")
                    st.write(f"- URL: {get_session_state('repo_url')}")
                    st.write(f"- Framework: {analysis.get('framework', 'Unknown')}")
                    st.write(f"- Language: {analysis.get('language', 'Unknown')}")
                    
                    st.write("**Cloud Configuration:**")
                    st.write(f"- Provider: {cloud_config.get('provider', 'Unknown').upper()}")
                    if cloud_config.get('custom_domain'):
                        st.write(f"- Custom Domain: {cloud_config['custom_domain']}")
            
            with col2:
                if st.button("🚀 Deploy Now", type="primary", use_container_width=True):
                    with st.spinner("Starting deployment..."):
                        project_id = get_session_state("analysis_result", {}).get("project_id")
                        if project_id:
                            deploy_data = {
                                "project_id": project_id,
                                "provider": cloud_config["provider"],
                                "credentials": cloud_config["credentials"],
                                "custom_domain": cloud_config.get("custom_domain")
                            }
                            
                            deployment = api_client.deploy_project(deploy_data)
                            if deployment and deployment.get("success"):
                                set_session_state("deployment_id", deployment["deployment_id"])
                                set_session_state("deployment_status", "in_progress")
                                st.success("Deployment started!")
                                st.rerun()
                            else:
                                st.error("Failed to start deployment")
        else:
            render_deployment_status(api_client)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.checkbox("📊 Show Recent Deployments", value=False):
        st.header("📊 Recent Deployments")
        
        with st.spinner("Loading recent deployments..."):
            recent_deployments = api_client.get_recent_deployments()
            
            if recent_deployments:
                for deployment in recent_deployments.get("deployments", []):
                    render_deployment_card(deployment)
            else:
                st.info("No recent deployments found.")

def render_deployment_card(deployment: Dict[str, Any]):
    status = deployment.get("status", "unknown")
    provider = deployment.get("provider", "unknown").upper()
    
    if status == "completed":
        status_color = "status-success"
        status_icon = "✅"
    elif status == "failed":
        status_color = "status-error"
        status_icon = "❌"
    elif status == "in_progress":
        status_color = "status-warning"
        status_icon = "🔄"
    else:
        status_color = ""
        status_icon = "❓"
    
    st.markdown(f"""
    <div class="deployment-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{status_icon} Deployment ID:</strong> {deployment.get('id', 'Unknown')[:12]}...<br>
                <strong>Provider:</strong> {provider}<br>
                <strong>Status:</strong> <span class="{status_color}">{status.title()}</span>
            </div>
            <div style="text-align: right;">
                <small>{deployment.get('created_at', 'Unknown')}</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if deployment.get("url"):
        st.markdown(f"🔗 **Live URL:** [{deployment['url']}]({deployment['url']})")

if __name__ == "__main__":
    main()