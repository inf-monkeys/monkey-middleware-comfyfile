import { Redis } from "ioredis";
import { createLogger } from './logger.js';

import config from "./config.js";

const redis = new Redis({
  host: config.redis.host,
  port: config.redis.port,
  password: config.redis.password,
  db: config.redis.db || 0,
});

// 创建 logger 实例
const logger = createLogger('redis');

export default redis;

// 可以添加进程退出时的清理
process.on('SIGTERM', async () => {
  await redis.quit();
  process.exit(0);
});

process.on('SIGINT', async () => {
  await redis.quit();
  process.exit(0);
});
