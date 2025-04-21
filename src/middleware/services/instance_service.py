import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading
import time
import logging
from config import load_config, save_config
from ..models.instance import InstanceResponse

logger = logging.getLogger(__name__)

class InstanceService:
    def __init__(self):
        self.config = load_config()
        self.instances = self.config["comfyfile_instances"]
        self._health_check_lock = threading.Lock()
        self._last_check_time = datetime.now()
        self._check_interval = self.config["health_check"]["interval"]
        self._check_timeout = self.config["health_check"]["timeout"]
        logger.info(f"初始化实例服务，当前实例数量: {len(self.instances)}")
        self._start_health_check()

    def _start_health_check(self):
        """启动健康检查线程"""
        def health_check_loop():
            while True:
                current_time = datetime.now()
                time_diff = (current_time - self._last_check_time).total_seconds()
                
                if time_diff >= self._check_interval:
                    with self._health_check_lock:
                        if (current_time - self._last_check_time).total_seconds() >= self._check_interval:
                            self._perform_health_check()
                            self._last_check_time = current_time
                
                time.sleep(1)  # 每秒检查一次是否需要执行健康检查

        health_check_thread = threading.Thread(target=health_check_loop, daemon=True)
        health_check_thread.start()
        logger.info("健康检查线程已启动")

    def _perform_health_check(self):
        """执行健康检查"""
        logger.debug("开始执行健康检查")
        for instance in self.instances:
            health_status = self._check_instance_health(instance)
            instance["healthz"] = health_status
            instance["last_check"] = datetime.now()
            logger.debug(f"检查实例 {instance['url']} 健康状态: {health_status}")
        
        # 保存更新后的实例状态
        self.config["comfyfile_instances"] = self.instances
        save_config(self.config)
        logger.info(f"健康检查完成，当前实例状态: {[{'url': i['url'], 'healthz': i['healthz']} for i in self.instances]}")

    def _make_request(self, instance: Dict[str, Any], method: str, path: str, **kwargs) -> requests.Response:
        """发送请求到 Comfyfile 实例"""
        headers = kwargs.get("headers", {})
        if instance["token"]:
            headers["Authorization"] = f"Bearer {instance['token']}"
        kwargs["headers"] = headers
        url = f"{instance['url']}/comfyfile/{path}"
        logger.debug(f"发送请求到 {url}, 方法: {method}")
        return requests.request(method, url, **kwargs)

    def _check_instance_health(self, instance: Dict[str, Any]) -> bool:
        """检查实例健康状态"""
        try:
            response = self._make_request(instance, "GET", "healthz", timeout=self._check_timeout)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"检查实例 {instance['url']} 健康状态失败: {str(e)}")
            return False

    def get_available_instance(self) -> Optional[Dict[str, Any]]:
        """获取可用的 Comfyfile 实例"""
        with self._health_check_lock:
            for instance in self.instances:
                if not instance.get("busy", False) and instance.get("healthz", False):
                    logger.debug(f"找到可用实例: {instance['url']}")
                    return instance
            logger.warning("没有找到可用的实例")
            return None

    def get_default_instance(self) -> Optional[Dict[str, Any]]:
        """获取默认实例"""
        instance = self.instances[0] if self.instances else None
        logger.debug(f"获取默认实例: {instance['url'] if instance else 'None'}")
        return instance

    def add_instance(self, instance: Dict[str, str]) -> Dict[str, str]:
        """添加新实例"""
        logger.info(f"添加新实例: {instance['url']}")
        new_instance = {
            "url": instance["url"],
            "token": instance.get("token", ""),
            "busy": False,
            "last_check": datetime.now(),
            "healthz": True
        }
        with self._health_check_lock:
            self.instances.append(new_instance)
            self.config["comfyfile_instances"] = self.instances
            save_config(self.config)
        logger.info(f"实例添加成功，当前实例数量: {len(self.instances)}")
        return {"status": "success"}

    def remove_instance(self, instance_url: str) -> Dict[str, str]:
        """移除实例"""
        logger.info(f"尝试移除实例: {instance_url}")
        with self._health_check_lock:
            for i, instance in enumerate(self.instances):
                if instance["url"] == instance_url:
                    if instance.get("busy", False):
                        logger.warning(f"无法移除实例 {instance_url}，因为实例正忙")
                        raise ValueError("Instance is busy")
                    self.instances.pop(i)
                    self.config["comfyfile_instances"] = self.instances
                    save_config(self.config)
                    logger.info(f"实例 {instance_url} 已成功移除")
                    return {"status": "success"}
        logger.warning(f"未找到实例: {instance_url}")
        raise ValueError("Instance not found")

    def get_all_instances(self) -> List[InstanceResponse]:
        """获取所有实例状态（不包含敏感信息）"""
        logger.debug("获取所有实例状态")
        return [
            InstanceResponse(
                url=instance["url"],
                busy=instance.get("busy", False),
                last_check=instance.get("last_check"),
                healthz=instance.get("healthz", False)
            )
            for instance in self.instances
        ]

    def make_request(self, instance: Dict[str, Any], method: str, path: str, **kwargs) -> requests.Response:
        """发送请求到 Comfyfile 实例"""
        logger.debug(f"发送请求到实例 {instance['url']}，路径: {path}，方法: {method}")
        return self._make_request(instance, method, path, **kwargs) 