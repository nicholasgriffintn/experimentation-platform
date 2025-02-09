from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)