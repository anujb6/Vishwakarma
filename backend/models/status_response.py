from pydantic import BaseModel
from typing import List, Optional

class StatusResponse(BaseModel):
    deployment_id: str
    status: str
    url: Optional[str]
    logs: List[str]
    created_at: str
    completed_at: Optional[str]
