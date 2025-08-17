from typing import Any, Dict
from pydantic import BaseModel

class AnalyzeResponse(BaseModel):
    success: bool
    project_id: str
    analysis: Dict[str, Any]
    supported: bool
    message: str