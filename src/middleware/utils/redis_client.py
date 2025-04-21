import redis
from config import load_config
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    
    def __init__(self):
        if RedisClient._instance is not None:
            raise Exception("This class is a singleton!")
        
        self.config = load_config()
        redis_config = self.config["redis"]
        
        # Redis 连接配置
        self.redis_client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            password=redis_config["password"],
            db=redis_config["db"],
            socket_timeout=30,  # 增加 socket 超时时间
            socket_connect_timeout=30,  # 增加连接超时时间
            retry_on_timeout=True,  # 超时后重试
            health_check_interval=30,  # 健康检查间隔
            max_connections=10  # 最大连接数
        )
        
        RedisClient._instance = self
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisClient()
        return cls._instance
    
    def get_client(self):
        return self.redis_client
    
    def test_connection(self):
        """测试 Redis 连接"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {str(e)}")
            return False 