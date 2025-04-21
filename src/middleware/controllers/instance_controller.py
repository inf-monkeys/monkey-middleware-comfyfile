from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from ..services.instance_service import InstanceService
from ..models.instance import Instance, InstanceResponse

router = APIRouter()
instance_service = InstanceService()

@router.get("/comfyfile/instances", response_model=List[InstanceResponse])
async def get_instances():
    """获取所有实例状态"""
    return instance_service.get_all_instances()

@router.post("/comfyfile/instances")
async def add_instance(instance: Instance):
    """添加新实例"""
    try:
        return instance_service.add_instance(instance.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/comfyfile/instances/{instance_url}")
async def remove_instance(instance_url: str):
    """移除实例"""
    try:
        return instance_service.remove_instance(instance_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) 