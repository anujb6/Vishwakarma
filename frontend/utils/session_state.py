import streamlit as st
from typing import Any, Optional

def init_session_state():
    defaults = {
        "current_step": 1,
        "step_repo_done": False,
        "step_cloud_done": False,
        "step_deploy_done": False,
        "repo_url": "",
        "repo_branch": "main",
        "analysis_result": None,
        "cloud_config": None,
        "selected_provider": None,
        "deployment_id": None,
        "deployment_status": None,
        "deployment_url": None,
        "last_status_check": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_session_state(key: str, default: Any = None) -> Any:
    return st.session_state.get(key, default)

def set_session_state(key: str, value: Any):
    st.session_state[key] = value

def clear_session_state(keys: list = None):
    if keys:
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]
    else:
        st.session_state.clear()

def reset_deployment_state():
    deployment_keys = [
        "deployment_id", 
        "deployment_status", 
        "deployment_url",
        "last_status_check",
        "step_deploy_done"
    ]
    clear_session_state(deployment_keys)