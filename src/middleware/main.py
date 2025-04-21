from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .middleware.security import SecurityMiddleware
from .controllers import task_router, instance_router, proxy_router
from .config.logging_config import setup_logging
import os

# 根据环境变量设置日志级别
debug = os.getenv("DEBUG", "false").lower() == "true"
logger = setup_logging(debug=debug)

app = FastAPI(
    title="ComfyFile Middleware",
    description="Middleware service for ComfyFile task management",
    version="1.0.0"
)

# 安全中间件
app.add_middleware(SecurityMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(task_router)
app.include_router(instance_router)
app.include_router(proxy_router)

@app.get("/")
async def root():
    logger.info("访问根路径")
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version
    }