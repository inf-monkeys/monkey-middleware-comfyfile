from fastapi import Request, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional, Callable, Awaitable
from config import load_config
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.responses import JSONResponse

class SecurityMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app
        self.config = load_config()
        self.secret = self.config["security"]["secret"]
        # 同时支持 Bearer token 和 query 两种方式
        self.header_key = APIKeyHeader(name="Authorization")
        self.query_key = APIKeyQuery(name="api_key")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        验证请求的 API Key，支持 Bearer token 和 query 两种方式
        
        Args:
            scope: ASGI scope
            receive: ASGI receive
            send: ASGI send
        """
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        try:
            # 尝试从 header 获取 Bearer token
            try:
                auth_header = await self.header_key(request)
                if not auth_header.startswith("Bearer "):
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid Authorization header format"
                    )
                api_key = auth_header.split(" ")[1]
            except:
                # 如果 header 中没有，尝试从 query 获取
                api_key = await self.query_key(request)
            
            # 验证 API Key
            if api_key != self.secret:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API Key"
                )
            
            # 验证通过，继续处理请求
            await self.app(scope, receive, send)
        except HTTPException as e:
            # 处理 HTTPException
            response = JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
            await response(scope, receive, send)
        except Exception as e:
            # 处理其他异常
            response = JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"}
            )
            await response(scope, receive, send) 