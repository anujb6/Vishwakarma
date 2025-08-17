from pydantic import BaseModel


class DeployResponse(BaseModel):
    success: bool
    deployment_id: str
    message: str
    status: str