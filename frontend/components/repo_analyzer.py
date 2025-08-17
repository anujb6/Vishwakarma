import streamlit as st
import re
from typing import Dict, Any, Optional
from utils.session_state import get_session_state, set_session_state

def render_repo_analyzer(api_client) -> Optional[Dict[str, Any]]:
    
    st.subheader("📁 Enter Your Repository Details")
    
    repo_url = st.text_input(
        "Repository URL",
        value=get_session_state("repo_url", ""),
        placeholder="https://github.com/username/repository",
        help="Enter the Git repository URL (GitHub, GitLab, Bitbucket, etc.)"
    )
    
    col1, col2 = st.columns([2, 1])
    with col1:
        branch = st.text_input(
            "Branch",
            value=get_session_state("repo_branch", "main"),
            help="Git branch to deploy (default: main)"
        )
    
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 Analyze Repository", type="primary", use_container_width=True)
    
    if repo_url:
        if not _validate_repo_url(repo_url):
            st.error("❌ Please enter a valid Git repository URL")
            return None
        else:
            st.success("✅ Repository URL format is valid")
    
    if analyze_btn and repo_url:
        if not _validate_repo_url(repo_url):
            st.error("❌ Invalid repository URL format")
            return None
        
        set_session_state("repo_url", repo_url)
        set_session_state("repo_branch", branch)
        
        with st.spinner("🔄 Analyzing repository... This may take a minute."):
            analysis_result = api_client.analyze_repository(repo_url, branch)
            
            if analysis_result and analysis_result.get("success"):
                st.success("✅ Repository analysis completed!")
                
                analysis = analysis_result.get("analysis", {})
                supported = analysis_result.get("supported", False)
                
                _display_analysis_results(analysis, supported)
                
                if supported:
                    st.success("🎉 This framework is supported for deployment!")
                    return analysis_result
                else:
                    st.warning("⚠️ This framework is not currently supported for automatic deployment.")
                    st.info("Supported frameworks: React, Vue, Angular, Next.js, Gatsby, Static HTML")
                    return None
            else:
                st.error("❌ Failed to analyze repository. Please check the URL and try again.")
                if analysis_result and analysis_result.get("message"):
                    st.error(f"Error: {analysis_result['message']}")
                return None
    
    return None

def _validate_repo_url(url: str) -> bool:
    if not url:
        return False
    
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(url_pattern, url):
        return False
    
    git_hosts = [
        'github.com',
        'gitlab.com', 
        'bitbucket.org',
        'dev.azure.com',
        'git.sr.ht'
    ]
    
    return any(host in url.lower() for host in git_hosts)

def _display_analysis_results(analysis: Dict[str, Any], supported: bool):
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔧 Framework",
            value=analysis.get("framework", "Unknown").title()
        )
    
    with col2:
        st.metric(
            label="💻 Language", 
            value=analysis.get("language", "Unknown").title()
        )
    
    with col3:
        framework_status = "✅ Supported" if supported else "❌ Not Supported"
        st.metric(
            label="🎯 Status",
            value=framework_status
        )
    
    with st.expander("📊 Detailed Analysis", expanded=False):
        
        files_info = analysis.get("files", {})
        if files_info:
            st.subheader("📁 Project Files")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Total Files:** {files_info.get('total_files', 0)}")
                st.write(f"**Project Size:** {files_info.get('size_mb', 0)} MB")
                
            with col2:
                if files_info.get('has_dockerfile'):
                    st.write("🐳 **Docker:** Found")
                if files_info.get('has_readme'):
                    st.write("📖 **README:** Found")
        
        if analysis.get("build_command"):
            st.subheader("🔨 Build Configuration")
            st.code(analysis.get("build_command"), language="bash")
            st.write(f"**Output Directory:** {analysis.get('output_directory', 'build')}")
        
        if analysis.get("language") == "javascript":
            dependencies = analysis.get("dependencies", {})
            if dependencies:
                st.subheader("📦 Dependencies")
                
                key_deps = [dep for dep in dependencies.keys() if dep in [
                    'react', 'vue', 'angular', 'next', 'gatsby', 'svelte', 'vite'
                ]]
                
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

def _get_framework_icon(framework: str) -> str:
    icons = {
        "react": "⚛️",
        "vue": "💚", 
        "angular": "🅰️",
        "next": "▲",
        "gatsby": "🟣",
        "static": "📄",
        "svelte": "🧡",
        "nuxt": "💚"
    }
    return icons.get(framework.lower(), "🔧")