from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..services.task_service import TaskService
from ..services.instance_service import InstanceService

router = APIRouter()
instance_service = InstanceService()
task_service = TaskService(instance_service)

@router.post("/comfyfile/run")
async def run_workflow(data: Dict[str, Any]):
    """运行工作流 - 进入任务队列，等待任务完成"""
    try:
        return await task_service.run_workflow(data)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/comfyfile/run_async")
async def run_workflow_async(data: Dict[str, Any]):
    """运行工作流 - 进入任务队列，立即返回任务ID"""
    try:
        return await task_service.run_workflow_async(data)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comfyfile/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        return task_service.get_task_status(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) 