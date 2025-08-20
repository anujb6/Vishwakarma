#code_analyzer.py
import os
import json
from pathlib import Path
from typing import Dict, Any
import logging

from config import config

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.supported_frameworks = config.SUPPORTED_FRAMEWORKS
    
    def analyze_project(self, repo_path: str) -> Dict[str, Any]:
        try:
            analysis = {
                "language": None,
                "framework": None,
                "build_command": None,
                "output_directory": None,
                "package_manager": None,
                "is_static_site": False,
                "dependencies": {},
                "files": self._get_file_info(repo_path)
            }
            
            if self._has_file(repo_path, "package.json"):
                analysis.update(self._analyze_javascript_project(repo_path))
            elif self._has_file(repo_path, "requirements.txt"):
                analysis.update(self._analyze_python_project(repo_path))
            elif self._has_file(repo_path, "index.html"):
                analysis.update(self._analyze_static_project(repo_path))
            
            if analysis["framework"] in self.supported_frameworks:
                framework_config = self.supported_frameworks[analysis["framework"]]
                analysis["build_command"] = framework_config["build_cmd"]
                analysis["output_directory"] = framework_config["output_dir"]
                analysis["is_static_site"] = True
            
            logger.info(f"Analysis completed: {analysis['language']}/{analysis['framework']}")
            # print(f"Analysis: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing project: {e}")
            return {"error": str(e), "supported": False}
    
    def _has_file(self, repo_path: str, filename: str) -> bool:
        return os.path.exists(os.path.join(repo_path, filename))
    
    def _get_file_info(self, repo_path: str) -> Dict[str, Any]:
        file_info = {
            "total_files": 0,
            "file_extensions": {},
            "has_dockerfile": False,
            "has_readme": False,
            "size_mb": 0
        }
        
        try:
            total_size = 0
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
                
                for file in files:
                    if not file.startswith('.'):
                        file_info["total_files"] += 1
                        
                        ext = Path(file).suffix.lower()
                        file_info["file_extensions"][ext] = file_info["file_extensions"].get(ext, 0) + 1
                        
                        if file.lower() == "dockerfile":
                            file_info["has_dockerfile"] = True
                        elif file.lower().startswith("readme"):
                            file_info["has_readme"] = True
                        
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                        except OSError:
                            pass
            
            file_info["size_mb"] = round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
        
        return file_info
    
    def _analyze_javascript_project(self, repo_path: str) -> Dict[str, Any]:
        try:
            package_json_path = os.path.join(repo_path, "package.json")
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            dependencies = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {})
            }
            
            framework = self._detect_js_framework(dependencies)
            
            package_manager = "yarn" if self._has_file(repo_path, "yarn.lock") else "npm"
            
            return {
                "language": "javascript",
                "framework": framework,
                "package_manager": package_manager,
                "dependencies": dependencies,
                "scripts": package_data.get("scripts", {}),
                "node_version": package_data.get("engines", {}).get("node", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing JavaScript project: {e}")
            return {"language": "javascript", "framework": "unknown"}
    
    def _analyze_python_project(self, repo_path: str) -> Dict[str, Any]:
        try:
            framework = "unknown"
            dependencies = []
            
            if self._has_file(repo_path, "requirements.txt"):
                with open(os.path.join(repo_path, "requirements.txt"), 'r') as f:
                    requirements = f.read()
                    dependencies = [line.strip() for line in requirements.split('\n') if line.strip()]
                    
                    req_lower = requirements.lower()
                    if 'django' in req_lower:
                        framework = 'django'
                    elif 'flask' in req_lower:
                        framework = 'flask'
                    elif 'fastapi' in req_lower:
                        framework = 'fastapi'
                    elif 'streamlit' in req_lower:
                        framework = 'streamlit'
            
            return {
                "language": "python",
                "framework": framework,
                "dependencies": dependencies,
                "has_requirements": self._has_file(repo_path, "requirements.txt"),
                "has_setup_py": self._has_file(repo_path, "setup.py")
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Python project: {e}")
            return {"language": "python", "framework": "unknown"}
    
    def _analyze_static_project(self, repo_path: str) -> Dict[str, Any]:
        return {
            "language": "html",
            "framework": "static",
            "has_css": len([f for f in os.listdir(repo_path) if f.endswith('.css')]) > 0,
            "has_js": len([f for f in os.listdir(repo_path) if f.endswith('.js')]) > 0,
            "is_static_site": True
        }
    
    def _detect_js_framework(self, dependencies: Dict[str, str]) -> str:
        if 'next' in dependencies:
            return 'next'
        elif 'nuxt' in dependencies:
            return 'nuxt'  
        elif 'gatsby' in dependencies:
            return 'gatsby'
        elif '@angular/core' in dependencies:
            return 'angular'
        elif 'react' in dependencies or 'react-dom' in dependencies:
            return 'react'
        elif 'vue' in dependencies or '@vue/cli' in dependencies:
            return 'vue'
        elif 'svelte' in dependencies:
            return 'svelte'
        else:
            return 'unknown'