import uvicorn
import os
from src.middleware.main import app

if __name__ == "__main__":
    # 设置环境变量
    os.environ["DEBUG"] = "false"
    
    uvicorn.run(
        "src.middleware.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境关闭热重载
        log_level="info"
    ) 