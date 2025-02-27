"""
User context model.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Context information about a user."""

    user_id: str
    session_id: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
