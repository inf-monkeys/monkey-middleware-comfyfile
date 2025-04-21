# monkey-middleware-comfyfile

Comfyfile 的任务队列管理中间件。

## 功能特点

- 完全兼容 Comfyfile 的接口
- 支持多个 Comfyfile 实例的管理
- 任务队列和调度功能
- 自动选择空闲实例执行任务
- 实例健康检查
- 任务状态查询
- 实例动态管理
- 配置持久化
- 任务队列持久化
- 崩溃自动恢复
- 实例访问鉴权

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 方式一：直接运行
python run_debug.py
python run_prod.py

# 方式二：使用 uvicorn
uvicorn src.middleware.main:app --host 0.0.0.0 --port 8000 --reload
```

## 配置文件

参照 `config.example.yaml` 创建 `config.yaml` 文件：

## 项目结构

```
src/middleware/
├── controllers/         # 控制器层
│   ├── task_controller.py      # 任务相关接口
│   ├── instance_controller.py  # 实例管理接口
│   └── proxy_controller.py     # 请求转发
├── services/           # 服务层
│   ├── task_service.py        # 任务队列和状态管理
│   └── instance_service.py    # 实例管理和健康检查
├── models/            # 模型层
│   ├── task.py              # 任务相关模型
│   └── instance.py          # 实例相关模型
├── middleware/        # 中间件层
│   └── security.py          # 安全认证中间件
├── config/           # 配置层
│   └── logging_config.py    # 日志配置
├── config.py         # 配置文件读取
├── main.py          # 主应用入口
├── run_prod.py     # 生产环境启动脚本
└── run_debug.py     # 开发环境启动脚本
```

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