import os
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

from config import config

logger = logging.getLogger(__name__)

class BuildService:
    def __init__(self):
        self.build_timeout = config.BUILD_TIMEOUT_SECONDS

    async def build_project(self, repo_path: str, analysis: Dict[str, Any]) -> str:
        try:
            framework = analysis.get("framework")
            build_command = analysis.get("build_command")
            output_directory = analysis.get("output_directory", "build")

            logger.info(f"Starting build process for {framework} project")

            if not build_command:
                logger.info("No build command needed, using static files")
                return repo_path

            logger.info(f"Building {framework} project with command: {build_command}")

            await self._install_dependencies(repo_path, analysis)

            await self._run_build_command(repo_path, build_command)

            build_output_path = os.path.join(repo_path, output_directory)

            if not os.path.exists(build_output_path):
                raise Exception(f"Build output directory not found: {build_output_path}")

            if not any(Path(build_output_path).iterdir()):
                raise Exception("Build output directory is empty")

            logger.info(f"Build completed successfully: {build_output_path}")
            return build_output_path

        except Exception as e:
            logger.error(f"Build failed: {e}")
            raise Exception(f"Build failed: {str(e)}")

    async def _install_dependencies(self, repo_path: str, analysis: Dict[str, Any]):
        language = analysis.get("language")

        if language == "javascript":
            await self._install_js_dependencies(repo_path, analysis)
        elif language == "python":
            await self._install_python_dependencies(repo_path, analysis)

    async def _install_js_dependencies(self, repo_path: str, analysis: Dict[str, Any]):
        package_manager = analysis.get("package_manager", "npm")

        if not os.path.exists(os.path.join(repo_path, "package.json")):
            logger.warning("No package.json found, skipping dependency installation")
            return

        logger.info(f"Installing dependencies with {package_manager}")

        if package_manager == "yarn":
            install_cmd = "yarn install"
        else:
            if os.path.exists(os.path.join(repo_path, "package-lock.json")):
                install_cmd = "npm ci"
            else:
                install_cmd = "npm install"

        await self._run_command(install_cmd, repo_path, "Dependency installation failed")

    async def _install_python_dependencies(self, repo_path: str, analysis: Dict[str, Any]):
        requirements_path = os.path.join(repo_path, "requirements.txt")

        if not os.path.exists(requirements_path):
            logger.warning("No requirements.txt found, skipping dependency installation")
            return

        logger.info("Installing Python dependencies")
        cmd = f"pip install -r {requirements_path}"
        await self._run_command(cmd, repo_path, "Python dependency installation failed")

    async def _run_build_command(self, repo_path: str, build_command: str):
        logger.info(f"Executing build command: {build_command}")

        commands = [cmd.strip() for cmd in build_command.split("&&")]

        for i, cmd in enumerate(commands):
            logger.info(f"Running command {i+1}/{len(commands)}: {cmd}")
            await self._run_command(cmd, repo_path, f"Build command '{cmd}' failed")

        logger.info("All build commands completed successfully")

    async def _run_command(self, command: str, cwd: str, error_prefix: str):
        """Run a shell command safely on Windows & Linux"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.build_timeout,
                env=os.environ.copy()
            )
            if result.returncode != 0:
                logger.error(f"{error_prefix}: {result.stderr.strip() or result.stdout.strip()}")
                raise Exception(f"{error_prefix}: {result.stderr.strip() or result.stdout.strip()}")

            if result.stdout:
                logger.info(result.stdout.strip())
        except subprocess.TimeoutExpired:
            logger.error(f"{error_prefix}: Command timed out after {self.build_timeout}s")
            raise Exception(f"{error_prefix}: Command timed out after {self.build_timeout}s")

    def get_build_artifacts_info(self, build_path: str) -> Dict[str, Any]:
        try:
            artifacts_info = {
                "total_files": 0,
                "total_size_mb": 0,
                "file_types": {},
                "has_index_html": False,
                "static_assets": []
            }

            for root, dirs, files in os.walk(build_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, build_path)

                    artifacts_info["total_files"] += 1

                    try:
                        size = os.path.getsize(file_path)
                        artifacts_info["total_size_mb"] += size
                    except OSError:
                        continue

                    ext = Path(file).suffix.lower()
                    artifacts_info["file_types"][ext] = artifacts_info["file_types"].get(ext, 0) + 1

                    if file.lower() == "index.html":
                        artifacts_info["has_index_html"] = True

                    if ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']:
                        artifacts_info["static_assets"].append(rel_path)

            artifacts_info["total_size_mb"] = round(artifacts_info["total_size_mb"] / (1024 * 1024), 2)

            return artifacts_info

        except Exception as e:
            logger.error(f"Error getting build artifacts info: {e}")
            return {}
