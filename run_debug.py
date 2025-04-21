import uvicorn
import os
from src.middleware.main import app

if __name__ == "__main__":
    # 设置环境变量
    os.environ["DEBUG"] = "true"
    
    uvicorn.run(
        "src.middleware.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    ) 