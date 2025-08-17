from typing import List, Optional
from pydantic import BaseModel


class StatusResponse(BaseModel):
    deployment_id: str
    status: str
    url: Optional[str]
    logs: List[str]
    created_at: str
    completed_at: Optional[str]