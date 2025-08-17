from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import uuid
from datetime import datetime

from backend.models.analyze_request import AnalyzeRequest
from backend.models.analyze_response import AnalyzeResponse
from backend.models.deploy_request import DeployRequest
from backend.models.deploy_response import DeployResponse
from backend.models.status_response import StatusResponse
from backend.services.git_service import GitService
from backend.services.code_analyzer import CodeAnalyzer
from backend.services.deployment_manager import DeploymentManager
from backend.utils.validation import validate_repo_url, validate_credentials

logger = logging.getLogger(__name__)
router = APIRouter()

git_service = GitService()
code_analyzer = CodeAnalyzer()
deployment_manager = DeploymentManager()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest):
    try:
        if not validate_repo_url(str(request.repo_url)):
            raise HTTPException(status_code=400, detail="Invalid repository URL")
        
        logger.info(f"Analyzing repository: {request.repo_url}")
        
        repo_path = await git_service.clone_repository(
            str(request.repo_url), 
            request.branch
        )
        
        analysis = code_analyzer.analyze_project(repo_path)
        
        project_id = str(uuid.uuid4())
        project_data = {
            "id": project_id,
            "repo_url": str(request.repo_url),
            "branch": request.branch,
            "repo_path": repo_path,
            "analysis": analysis,
            "created_at": datetime.now().isoformat()
        }
        
        deployment_manager.save_project(project_id, project_data)
        
        supported = analysis.get("framework") in ["react", "vue", "angular", "next", "static", "gatsby"]
        
        return AnalyzeResponse(
            success=True,
            project_id=project_id,
            analysis=analysis,
            supported=supported,
            message="Repository analyzed successfully" if supported else "Framework not supported for deployment"
        )
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deploy", response_model=DeployResponse)
async def deploy_project(request: DeployRequest, background_tasks: BackgroundTasks):
    try:
        if request.provider not in ["aws", "azure"]:
            raise HTTPException(status_code=400, detail="Unsupported cloud provider")
        
        if not validate_credentials(request.provider, request.credentials):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        project_data = deployment_manager.get_project(request.project_id)
        if not project_data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        deployment_id = str(uuid.uuid4())
        
        logger.info(f"Starting deployment {deployment_id} for project {request.project_id}")
        
        background_tasks.add_task(
            deployment_manager.deploy_project,
            deployment_id,
            project_data,
            request.provider,
            request.credentials,
            request.custom_domain
        )
        
        return DeployResponse(
            success=True,
            deployment_id=deployment_id,
            message="Deployment started",
            status="in_progress"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting deployment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{deployment_id}", response_model=StatusResponse)
async def get_deployment_status(deployment_id: str):
    try:
        deployment_data = deployment_manager.get_deployment(deployment_id)
        if not deployment_data:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return StatusResponse(
            deployment_id=deployment_id,
            status=deployment_data.get("status", "unknown"),
            url=deployment_data.get("url"),
            logs=deployment_data.get("logs", []),
            created_at=deployment_data.get("created_at"),
            completed_at=deployment_data.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/deployments")
async def list_deployments(limit: int = 10, offset: int = 0):
    try:
        deployments = deployment_manager.list_deployments(limit, offset)
        return {
            "deployments": deployments,
            "total": len(deployments)
        }
    except Exception as e:
        logger.error(f"Error listing deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))