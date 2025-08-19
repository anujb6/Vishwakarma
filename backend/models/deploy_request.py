from typing import Dict, Optional
from pydantic import BaseModel


class DeployRequest(BaseModel):
    project_id: str
    provider: str
    credentials: Dict[str, Optional[str]]
    custom_domain: Optional[str] = None