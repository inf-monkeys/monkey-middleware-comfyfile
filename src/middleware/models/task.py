from datetime import datetime
from typing import Any, Optional, Dict
from pydantic import BaseModel

class TaskStatus(BaseModel):
    status: str  # pending, running, completed, failed
    instance_url: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None

class Task(BaseModel):
    id: str
    data: Dict[str, Any] 