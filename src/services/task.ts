import ComfyfileInstance from '../models/ComfyfileInstance.js';
import { getAvailableInstance, setInstanceBusy } from './instance.js';
import redis from '../utils/redis.js';
import { nanoid } from 'nanoid';
import { createLogger } from '../utils/logger.js';
import { ComfyfileTaskResult } from '../typings/ComfyfileTask.js';

// 创建 logger 实例
const logger = createLogger('task-service');

// 任务队列名称
const TASK_QUEUE = 'comfyfile:tasks';

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// 任务类型定义
interface WorkflowTask {
  id: string;
  instanceId?: string;
  params: any;
  timestamp: number;
  status?: TaskStatus;
  retries?: number;
  result?: any;
}

// 推送工作流任务到队列
export async function pushWorkflowTask(params: string): Promise<string> {
  const taskId = nanoid();
  const task: WorkflowTask = {
    id: taskId,
    params,
    timestamp: Date.now(),
    status: TaskStatus.PENDING,
    retries: 0
  };
  
  // 将任务推送到 Redis 队列
  await redis.lpush(TASK_QUEUE, JSON.stringify(task));
  
  // 同时在Redis中存储任务状态，便于查询
  await redis.set(`comfyfile:task:${taskId}`, JSON.stringify(task));
  
  logger.info(`任务 ${taskId} 已添加到队列`);
  
  // 触发任务处理
  processNextTask();
  
  return taskId;
}

// 获取任务状态
export async function getTaskStatus(taskId: string): Promise<WorkflowTask | null> {
  const taskJson = await redis.get(`comfyfile:task:${taskId}`);
  if (!taskJson) return null;
  return JSON.parse(taskJson);
}

// 更新任务状态并发布结果
async function updateTaskStatus(taskId: string, status: TaskStatus, data?: ComfyfileTaskResult): Promise<void> {
  const taskJson = await redis.get(`comfyfile:task:${taskId}`);
  if (!taskJson) return;
  
  const task: WorkflowTask = JSON.parse(taskJson);
  task.status = status;
  
  if (data) {
    task.result = data;
  }
  
  await redis.set(`comfyfile:task:${taskId}`, JSON.stringify(task));
  
  // 当任务完成或失败时，发布结果通知
  if (status === TaskStatus.COMPLETED || status === TaskStatus.FAILED) {
    const resultPayload = status === TaskStatus.COMPLETED 
      ? { data: task.result }
      : { error: "任务执行失败" };
      
    await redis.publish(`comfyfile:result:${taskId}`, JSON.stringify(resultPayload));
    logger.info(`已发布任务 ${taskId} 的${status === TaskStatus.COMPLETED ? '完成' : '失败'}结果`);
  }
}

// 运行工作流
export async function runWorkflow(params: string): Promise<ComfyfileTaskResult> {
  return new Promise(async (resolve, reject) => {
    // 先获取任务ID，确保它是一个确定的值
    const taskId = await pushWorkflowTask(params);
    logger.info(`开始监听任务 ${taskId} 的结果`);
    
    // 创建一个任务结果监听器
    const resultKey = `comfyfile:result:${taskId}`;
    
    // 设置超时
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error('任务执行超时'));
    }, 2 * 60 * 60 * 1000); // 2 小时
    
    // 监听任务结果
    const subscriber = redis.duplicate();
    
    // 确保在订阅前设置消息处理程序
    subscriber.on('message', (channel: string, message: string) => {
      logger.info(`收到频道 ${channel} 的消息:`, message);
      if (channel === resultKey) {
        cleanup();
        try {
          const result = JSON.parse(message);
          if (result.error) {
            reject(new Error(result.error));
          } else {
            resolve(result.data);
          }
        } catch (e) {
          reject(e);
        }
      }
    });
    
    // 订阅频道
    subscriber.subscribe(resultKey, (err: any) => {
      if (err) {
        logger.error(`订阅频道 ${resultKey} 失败:`, err);
        cleanup();
        reject(err);
      } else {
        logger.info(`成功订阅频道 ${resultKey}`);
      }
    });
    
    function cleanup() {
      logger.info(`清理任务 ${taskId} 的资源`);
      clearTimeout(timeout);
      subscriber.unsubscribe(resultKey);
      subscriber.quit();
    }
  });
}

// 处理下一个任务
export async function processNextTask() {
  while (true) {
    // 检查是否有可用实例
    const instance = getAvailableInstance();
    if (!instance) {
      logger.info('没有可用的实例，任务将保持在队列中');
      return;
    }
    
    // 使用BRPOP阻塞式获取任务
    const taskResult = await redis.brpop(TASK_QUEUE, 1);
    if (!taskResult) {
      return;
    }
    
    // BRPOP返回的是[key, value]数组
    const taskJson = taskResult[1];
    
    try {
      const task: WorkflowTask = JSON.parse(taskJson);
      logger.info(`开始处理任务 ${task.id} 使用实例 ${instance.url}`);
      
      // 标记实例为忙碌状态
      setInstanceBusy(instance, true);
      
      // 执行任务
      try {
        await executeTask(task, instance);
        // 注意：结果发布已经在 updateTaskStatus 中处理
      } catch (error) {
        // 错误处理已经在 executeTask 和 updateTaskStatus 中完成
        logger.error(`处理任务 ${task.id} 时出错:`, error);
      } finally {
        // 标记实例为可用状态
        setInstanceBusy(instance, false);
      }
    } catch (error) {
      logger.error('处理任务时出错:', error);
      if (instance) {
        setInstanceBusy(instance, false);
      }
    }
  }
}

// 执行任务 - 添加重试逻辑
async function executeTask(task: WorkflowTask, instance: ComfyfileInstance): Promise<any> {
  try {
    // 更新任务状态为处理中
    await updateTaskStatus(task.id, TaskStatus.PROCESSING);
    
    // 使用实例的 axiosInstance 转发请求到 /comfyfile/run 路由
    const response = await instance.axiosInstance.post('/comfyfile/run', task.params);
    
    // 更新任务状态为完成
    await updateTaskStatus(task.id, TaskStatus.COMPLETED, response.data);
    
    return response.data;
  } catch (error) {
    logger.error(`任务 ${task.id} 执行失败:`, error);
    
    // 更新任务状态为失败
    await updateTaskStatus(task.id, TaskStatus.FAILED);
    
    throw error;
  }
}

// 启动任务处理器 - 改进版本
export function startTaskProcessor() {
  // 不再需要定期轮询，直接启动处理
  processNextTask();
  logger.info('ComfyFile 任务处理器已启动');
}

// 获取所有任务列表
export async function getAllTasks(limit: number = 100, offset: number = 0): Promise<WorkflowTask[]> {
  // 使用Redis的SCAN命令获取所有任务键
  const tasks: WorkflowTask[] = [];
  let cursor = '0';
  
  do {
    // 使用SCAN命令获取键
    const [nextCursor, keys] = await redis.scan(
      cursor, 
      'MATCH', 
      'comfyfile:task:*', 
      'COUNT', 
      '100'
    );
    
    cursor = nextCursor;
    
    if (keys.length > 0) {
      // 批量获取任务数据
      const taskJsons = await redis.mget(...keys);
      
      for (const json of taskJsons) {
        if (json) {
          tasks.push(JSON.parse(json));
        }
      }
    }
  } while (cursor !== '0' && tasks.length < limit + offset);
  
  // 应用分页
  return tasks
    .sort((a, b) => b.timestamp - a.timestamp) // 按时间倒序
    .slice(offset, offset + limit);
}

// 获取特定状态的任务
export async function getTasksByStatus(status: TaskStatus, limit: number = 100): Promise<WorkflowTask[]> {
  const allTasks = await getAllTasks(1000); // 获取较大数量的任务
  return allTasks
    .filter(task => task.status === status)
    .slice(0, limit);
}

// 清理过期任务（可选，用于维护）
export async function cleanupOldTasks(olderThanDays: number = 7): Promise<number> {
  const cutoffTime = Date.now() - (olderThanDays * 24 * 60 * 60 * 1000);
  const allTasks = await getAllTasks(10000);
  
  let deletedCount = 0;
  
  for (const task of allTasks) {
    if (task.timestamp < cutoffTime && 
        (task.status === TaskStatus.COMPLETED || task.status === TaskStatus.FAILED)) {
      await redis.del(`comfyfile:task:${task.id}`);
      deletedCount++;
    }
  }
  
  return deletedCount;
}
