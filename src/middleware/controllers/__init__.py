from .task_controller import router as task_router
from .instance_controller import router as instance_router
from .proxy_controller import router as proxy_router

__all__ = ['task_router', 'instance_router', 'proxy_router'] 