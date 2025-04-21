from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from ..services.instance_service import InstanceService

router = APIRouter()
instance_service = InstanceService()

@router.api_route("/comfyfile/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(path: str, request: Request):
    """转发请求到默认实例"""
    try:
        # 获取默认实例
        instance = instance_service.get_default_instance()
        if not instance:
            raise HTTPException(status_code=503, detail="No available Comfyfile instance")

        # 获取请求数据
        method = request.method
        data = await request.json() if method in ["POST", "PUT"] else None

        # 发送请求
        response = instance_service.make_request(
            instance=instance,
            method=method,
            path=path,
            json=data
        )

        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 