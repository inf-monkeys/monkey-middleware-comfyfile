import json
import threading
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import redis
from config import load_config
from ..models.task import TaskStatus
from .instance_service import InstanceService

class TaskService:
    def __init__(self, instance_service: InstanceService):
        self.instance_service = instance_service
        self.config = load_config()
        self.redis_client = redis.Redis(
            host=self.config["redis"]["host"],
            port=self.config["redis"]["port"],
            password=self.config["redis"]["password"],
            db=self.config["redis"]["db"]
        )
        self._start_queue_processor()
        self._start_result_listener()

    def _start_result_listener(self):
        """启动结果监听线程"""
        def listen_for_results():
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe("task_results")
            
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        result = json.loads(message["data"])
                        task_id = result["task_id"]
                        if "error" in result:
                            # 处理错误
                            self.redis_client.set(f"task:{task_id}:error", result["error"])
                            print(f"任务 {task_id} 执行失败: {result['error']}")  # 在控制台打印错误
                        else:
                            # 处理成功结果
                            self.redis_client.set(f"task:{task_id}:result", json.dumps(result["data"]))
                    except Exception as e:
                        print(f"处理结果时出错: {e}")

        listener_thread = threading.Thread(target=listen_for_results, daemon=True)
        listener_thread.start()

    def _start_queue_processor(self):
        """启动队列处理线程"""
        def process_queue():
            while True:
                try:
                    # 从 Redis 获取任务
                    task_data = self.redis_client.lpop("task_queue")
                    if task_data:
                        task = json.loads(task_data)
                        task_id = task["id"]
                        
                        # 更新任务状态为运行中
                        task_status = TaskStatus(
                            status="running",
                            start_time=datetime.now()
                        )
                        self.redis_client.set(f"task:{task_id}", task_status.json())
                        
                        instance = self.instance_service.get_available_instance()
                        if instance:
                            instance["busy"] = True
                            try:
                                # 执行任务
                                response = self.instance_service.make_request(
                                    instance,
                                    "POST",
                                    "run",
                                    json=task["data"]
                                )
                                # 更新任务状态
                                task_status.status = "completed"
                                task_status.end_time = datetime.now()
                                task_status.result = response.json()
                                task_status.instance_url = instance["url"]
                                self.redis_client.set(f"task:{task_id}", task_status.json())
                                
                                # 发布结果
                                self.redis_client.publish(
                                    "task_results",
                                    json.dumps({
                                        "task_id": task_id,
                                        "data": response.json()
                                    })
                                )
                            except Exception as e:
                                error_msg = str(e)
                                print(f"任务 {task_id} 执行失败: {error_msg}")  # 在控制台打印错误
                                
                                task_status.status = "failed"
                                task_status.end_time = datetime.now()
                                task_status.error = error_msg
                                self.redis_client.set(f"task:{task_id}", task_status.json())
                                
                                # 发布错误
                                self.redis_client.publish(
                                    "task_results",
                                    json.dumps({
                                        "task_id": task_id,
                                        "error": error_msg
                                    })
                                )
                            finally:
                                instance["busy"] = False
                        else:
                            # 如果没有可用实例，将任务重新放回队列
                            self.redis_client.rpush("task_queue", json.dumps(task))
                            task_status.status = "pending"
                            self.redis_client.set(f"task:{task_id}", task_status.json())
                except Exception as e:
                    print(f"处理队列时出错: {e}")
                time.sleep(0.1)

        queue_thread = threading.Thread(target=process_queue, daemon=True)
        queue_thread.start()

    async def run_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """运行工作流 - 进入任务队列，等待任务完成"""
        task_id = str(datetime.now().timestamp())
        
        # 将任务添加到 Redis 队列
        task = {
            "id": task_id,
            "data": data
        }
        self.redis_client.rpush("task_queue", json.dumps(task))
        
        # 初始化任务状态
        task_status = TaskStatus(status="pending")
        self.redis_client.set(f"task:{task_id}", task_status.json())
        
        # 等待结果
        while True:
            # 检查错误
            error = self.redis_client.get(f"task:{task_id}:error")
            if error:
                error_msg = error.decode()
                print(f"任务 {task_id} 执行失败: {error_msg}")  # 在控制台打印错误
                return {"error": error_msg, "task_id": task_id}
            
            # 检查结果
            result = self.redis_client.get(f"task:{task_id}:result")
            if result:
                return json.loads(result)
            
            # 检查任务状态
            task_status_data = self.redis_client.get(f"task:{task_id}")
            if task_status_data:
                task_status = TaskStatus.parse_raw(task_status_data)
                if task_status.status == "failed":
                    error_msg = task_status.error or "Task failed"
                    print(f"任务 {task_id} 执行失败: {error_msg}")  # 在控制台打印错误
                    return {"error": error_msg, "task_id": task_id}
            
            await asyncio.sleep(0.1)

    async def run_workflow_async(self, data: Dict[str, Any]) -> Dict[str, str]:
        """运行工作流 - 异步执行，不等待任务完成"""
        task_id = str(datetime.now().timestamp())
        
        # 将任务添加到 Redis 队列
        task = {
            "id": task_id,
            "data": data
        }
        self.redis_client.rpush("task_queue", json.dumps(task))
        
        # 初始化任务状态
        task_status = TaskStatus(status="pending")
        self.redis_client.set(f"task:{task_id}", task_status.json())
        
        return {"task_id": task_id}

    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        task_data = self.redis_client.get(f"task:{task_id}")
        if task_data:
            return TaskStatus.parse_raw(task_data)
        return None 