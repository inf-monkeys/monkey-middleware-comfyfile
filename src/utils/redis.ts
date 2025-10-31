import { Redis } from "ioredis";
import { createLogger } from './logger.js';
import config from "./config.js";

// 创建 logger 实例
const logger = createLogger('redis');

let redis: Redis;

if (config.redis.sentinel?.enabled) {
  // Sentinel 模式
  redis = new Redis({
    sentinels: config.redis.sentinel.nodes.map(node => ({
      host: node.host,
      port: node.port
    })),
    name: config.redis.sentinel.master,
    password: config.redis.password,
    sentinelPassword: config.redis.sentinel.password,
    db: config.redis.db || 0,
  });
  
  logger.info(`Redis connecting in sentinel mode to master: ${config.redis.sentinel.master}`);
} else {
  // 普通模式
  redis = new Redis({
    host: config.redis.host,
    port: config.redis.port,
    username: config.redis.username,
    password: config.redis.password,
    db: config.redis.db || 0,
  });
  
  logger.info(`Redis connecting in standalone mode to: ${config.redis.host}:${config.redis.port}`);
}

// 添加连接事件监听
redis.on('connect', () => {
  logger.info('Redis connected successfully');
});

redis.on('error', (err) => {
  logger.error('Redis connection error:', err);
});

// 可以添加进程退出时的清理
process.on('SIGTERM', async () => {
  await redis.quit();
  process.exit(0);
});

process.on('SIGINT', async () => {
  await redis.quit();
  process.exit(0);
});

export default redis;
