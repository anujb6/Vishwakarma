from git import Optional
from pydantic import BaseModel, HttpUrl

class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = "main"