# monkey-middleware-comfyfile

Comfyfile 的任务队列管理中间件。

## 接口说明

### 任务相关
- `POST /comfyfile/run`: 运行工作流，进入任务队列，直到任务结束后返回数据
- `POST /comfyfile/run_async`: 运行工作流，进入任务队列，返回任务 id
- `GET /comfyfile/task/{task_id}`: 查询任务状态， 返回: 任务状态信息

### 实例管理
- `GET /comfyfile/instances`: 获取所有实例状态
- `POST /comfyfile/instances`: 添加新实例
  - 请求体: `{"url": "http://xxx:8188", "token": "your_token"}`
- `DELETE /comfyfile/instances/{instance_url}`: 移除实例

### 其他接口
- 其他 `/comfyfile/*` 接口：转发到默认实例

## 任务状态说明

任务状态包括：
- `pending`: 等待执行
- `running`: 正在执行
- `completed`: 执行完成
- `failed`: 执行失败

## 实例状态说明

实例状态包括：
- `url`: 实例地址
- `token`: 访问令牌
- `busy`: 是否正在执行任务
- `last_check`: 最后健康检查时间
- `healthz`: 是否健康