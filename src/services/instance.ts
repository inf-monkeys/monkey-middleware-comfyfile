import config from "../utils/config.js";
import ComfyfileInstance from '../models/ComfyfileInstance.js';
import { createLogger } from '../utils/logger.js';

// 创建 logger 实例
const logger = createLogger('instance-service');

// ComfyFile 实例数组
let comfyfileInstances: ComfyfileInstance[] = [];

// 健康检查间隔（毫秒）
const HEALTH_CHECK_INTERVAL = 60 * 1000; // 每分钟检查一次

// 初始化 ComfyFile 实例
export function initComfyfileInstances() {
  if (config.comfyfile_instances && Array.isArray(config.comfyfile_instances)) {
    comfyfileInstances = config.comfyfile_instances.map((instance) => new ComfyfileInstance({
      url: instance.url,
      token: instance.token,
    }));
    logger.info(`已初始化 ${comfyfileInstances.length} 个 ComfyFile 实例`);
    
    // 初始化后立即进行一次健康检查
    checkInstancesHealth();
    
    // 启动定时健康检查
    startHealthCheckScheduler();
  } else {
    logger.warn('未找到 ComfyFile 实例配置');
  }
}

// 启动健康检查定时器
function startHealthCheckScheduler() {
  setInterval(checkInstancesHealth, HEALTH_CHECK_INTERVAL);
  logger.info(`已启动实例健康检查定时任务，间隔: ${HEALTH_CHECK_INTERVAL / 1000}秒`);
}

// 检查所有实例的健康状态
async function checkInstancesHealth() {
  logger.info('开始检查所有实例的健康状态...');
  
  const checkPromises = comfyfileInstances.map(async (instance) => {
    try {
      await instance.checkHealth();
      logger.info(`实例 ${instance.url} 健康状态: ${instance.healthz ? '正常' : '异常'}`);
    } catch (error) {
      logger.error(`检查实例 ${instance.url} 健康状态失败:`, error);
      instance.healthz = false;
      instance.lastCheck = new Date();
    }
  });
  
  await Promise.all(checkPromises);
  logger.info('所有实例健康状态检查完成');
}

// 获取所有实例
export function getAllInstances(): ComfyfileInstance[] {
  return comfyfileInstances;
}

// 获取可用的实例
export function getAvailableInstance(): ComfyfileInstance | null {
  const availableInstance = comfyfileInstances.find(instance => 
    !instance.busy && instance.healthz === true
  );
  return availableInstance || null;
}

// 设置实例状态
export function setInstanceBusy(instance: ComfyfileInstance, busy: boolean): void {
  instance.busy = busy;
}

// 手动触发健康检查（可以通过API暴露此功能）
export async function triggerHealthCheck(): Promise<void> {
  await checkInstancesHealth();
}

// 获取实例健康状态摘要
export function getInstancesHealthSummary() {
  return comfyfileInstances.map(instance => ({
    url: instance.url,
    healthy: instance.healthz === true,
    lastCheck: instance.lastCheck,
    busy: instance.busy
  }));
}

