import streamlit as st
import requests
import urllib.parse
from typing import Any, Dict
from utils.session_state import get_session_state, set_session_state

CLIENT_ID = "Ov23liov0YrRLvIrHluW"
CLIENT_SECRET = "191d47d26d28819628ebdbc841d8caa25d071181"
REDIRECT_URI = "http://localhost:8501"
SCOPE = "repo"

def get_github_auth_url():
    """Generate GitHub OAuth authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'state': 'random_state_string'
    }
    return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token"""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Accept': 'application/json'}
    response = requests.post('https://github.com/login/oauth/access_token', 
                           data=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def render_repo_analyzer(api_client):
    st.subheader("📁 Select Your GitHub Repository")

    query_params = st.query_params
    
    if 'code' in query_params and 'token' not in st.session_state:
        code = query_params['code']
        token = exchange_code_for_token(code)
        if token:
            st.session_state.token = {'access_token': token}
            st.query_params.clear()
            st.rerun()
        else:
            st.error("❌ Failed to authenticate with GitHub")
            return None

    if "token" not in st.session_state:
        st.info("Please authenticate with GitHub to access your repositories")
        auth_url = get_github_auth_url()
        st.markdown(f'<a href="{auth_url}" target="_self" style="text-decoration: none;"><button style="background-color: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 16px;">🔑 Login with GitHub</button></a>', unsafe_allow_html=True)
        return None

    token = st.session_state.token["access_token"]

    headers = {"Authorization": f"token {token}"}
    
    try:
        resp = requests.get("https://api.github.com/user/repos", headers=headers)
        
        if resp.status_code != 200:
            st.error(f"❌ Failed to fetch repositories: {resp.status_code}")
            if resp.status_code == 401:
                del st.session_state.token
                st.rerun()
            return None

        repos = [repo["full_name"] for repo in resp.json()]
        
        if not repos:
            st.warning("No repositories found in your GitHub account")
            return None
            
        repo_name = st.selectbox("Select Repository", repos)

        if repo_name:
            branches_resp = requests.get(f"https://api.github.com/repos/{repo_name}/branches", headers=headers)
            
            if branches_resp.status_code == 200:
                branches_data = branches_resp.json()
                branch_names = [branch["name"] for branch in branches_data]
                
                default_branch = "main" if "main" in branch_names else (branch_names[0] if branch_names else "main")
                saved_branch = get_session_state("repo_branch", default_branch)
                
                try:
                    default_index = branch_names.index(saved_branch) if saved_branch in branch_names else 0
                except (ValueError, IndexError):
                    default_index = 0
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    branch = st.selectbox(
                        "Select Branch",
                        options=branch_names,
                        index=default_index,
                        help="Select the branch to analyze"
                    )
            else:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.warning("⚠️ Could not fetch branches, please enter manually")
                    branch = st.text_input(
                        "Branch",
                        value=get_session_state("repo_branch", "main"),
                        help="Git branch to deploy (default: main)",
                    )
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                branch = st.text_input(
                    "Branch",
                    value=get_session_state("repo_branch", "main"),
                    help="Git branch to deploy (default: main)",
                )

        with col2:
            st.write("")
            analyze_btn = st.button("🔍 Analyze Repository", type="primary", use_container_width=True)

        if analyze_btn and repo_name:
            repo_url = f"https://github.com/{repo_name}"
            set_session_state("repo_url", repo_url)
            set_session_state("repo_branch", branch)

            with st.spinner("🔄 Analyzing repository..."):
                analysis_result = api_client.analyze_repository(repo_url, branch)
                if analysis_result and analysis_result.get("success"):
                    st.success("✅ Repository analysis completed!")

                    analysis = analysis_result.get("analysis", {})
                    supported = analysis_result.get("supported", False)
                    set_session_state("analysis_result", analysis)
                    _display_analysis_results(analysis, supported)

                    return analysis_result
                else:
                    st.error("❌ Failed to analyze repository.")
                    return None

    except requests.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        return None

    return None

def _display_analysis_results(analysis: Dict[str, Any], supported: bool):
    framework = analysis.get("framework") or "Unknown"
    language = analysis.get("language") or "Unknown"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🔧 Framework", framework.capitalize())

    with col2:
        st.metric("💻 Language", language.capitalize())

    with col3:
        framework_status = "✅ Supported" if supported else "❌ Not Supported"
        st.metric("🎯 Status", framework_status)

    with st.expander("📊 Detailed Analysis", expanded=False):
        files_info = analysis.get("files", {})
        if files_info:
            st.subheader("📁 Project Files")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Total Files:** {files_info.get('total_files', 0)}")
                st.write(f"**Project Size:** {files_info.get('size_mb', 0)} MB")
            with col2:
                if files_info.get("has_dockerfile"):
                    st.write("🐳 **Docker:** Found")
                if files_info.get("has_readme"):
                    st.write("📖 **README:** Found")

        if analysis.get("build_command"):
            st.subheader("🔨 Build Configuration")
            st.code(analysis.get("build_command"), language="bash")
            st.write(f"**Output Directory:** {analysis.get('output_directory', 'build')}")

        if analysis.get("language") == "javascript":
            dependencies = analysis.get("dependencies", {})
            if dependencies:
                st.subheader("📦 Dependencies")
                key_deps = [
                    dep
                    for dep in dependencies.keys()
                    if dep in ["react", "vue", "angular", "next", "gatsby", "svelte", "vite"]
                ]
                if key_deps:
                    for dep in key_deps:
                        st.write(f"- **{dep}:** {dependencies[dep]}")
                if analysis.get("package_manager"):
                    st.write(f"**Package Manager:** {analysis.get('package_manager')}")

        file_extensions = files_info.get("file_extensions", {})
        if file_extensions:
            st.subheader("📄 File Types")
            sorted_extensions = sorted(file_extensions.items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_extensions[:10]:
                if ext:
                    st.write(f"**{ext}:** {count} files")