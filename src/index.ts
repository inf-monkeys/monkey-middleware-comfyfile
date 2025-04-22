import express from "express";

import config from "./utils/config.js";

import indexRouter from "./routes.js";
import authMiddleware from "./middlewares/auth.js";

import { getAllInstances, initComfyfileInstances } from './services/instance.js';
import { startTaskProcessor } from './services/task.js';

import { createLogger } from './utils/logger.js';

const app = express();

const port = config.server?.port || 8000;

app.use(express.json());

// 创建 logger 实例
const logger = createLogger('app');

app.get("/", (_, res) => {
  res.send({
    app: "monkey-middleware-comfyfile",
    version: "0.0.1",
    description: "Comfyfile 的任务队列管理中间件",
  });
});

if (config.security?.enabled)
  app.use(authMiddleware);

app.use("/comfyfile", indexRouter);

app.use('/', async (req, res) => {
  if (getAllInstances().length === 0) {
    res.status(500).json({
      success: false,
      error: 'No Comfyfile instances available'
    });
    return;
  }

  const instance = getAllInstances()[0];

  // 构建 Axios 请求配置
  const axiosConfig = {
    method: req.method,
    url: req.path,
    headers: req.headers,
    params: req.query,
    data: req.body,
  };

  try {
    const response = await instance.axiosInstance.request(axiosConfig);

    // 设置响应头
    if (response.headers) {
      Object.entries(response.headers).forEach(([key, value]) => {
        if (value) res.setHeader(key, value);
      });
    }

    // 返回响应数据
    res.status(response.status).send(response.data);
  } catch (error) {
    const status = (error as any).response?.status || 500;
    res.status(status).json({
      success: false,
      error: (error as any).message
    });
  }
});

// 初始化应用
async function initApp() {
  // 初始化 ComfyFile 实例
  initComfyfileInstances();

  // 启动任务处理器
  startTaskProcessor();

  logger.info(`服务器运行在 http://localhost:${port}`);

  app.listen(port, () => {
    logger.info(`服务器启动在端口 ${port}`);
  });
}

initApp();