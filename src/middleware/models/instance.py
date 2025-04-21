from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class InstanceStatus(BaseModel):
    url: str
    token: Optional[str] = None
    busy: bool = False
    last_check: Optional[datetime] = None
    healthz: bool = True

class Instance(BaseModel):
    url: str
    token: Optional[str] = None

class InstanceResponse(BaseModel):
    """用于返回给客户端的实例信息，不包含敏感信息"""
    url: str
    busy: bool
    last_check: Optional[datetime]
    healthz: bool 