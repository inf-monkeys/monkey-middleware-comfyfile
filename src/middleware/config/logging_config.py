import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import os
import time
from config import load_config

def setup_logging(debug: bool = False) -> logging.Logger:
    """
    设置日志配置
    
    Args:
        debug: 是否启用调试模式
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    config = load_config()
    log_config = config["logging"]
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器 - 普通日志
    file_handler = TimedRotatingFileHandler(
        log_dir / "middleware.log",
        when="midnight",  # 每天午夜轮转
        interval=log_config["rotation_interval"],  # 从配置文件读取轮转间隔
        backupCount=log_config["retention_days"],  # 从配置文件读取保留天数
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 文件处理器 - 错误日志
    error_handler = TimedRotatingFileHandler(
        log_dir / "error.log",
        when="midnight",  # 每天午夜轮转
        interval=log_config["rotation_interval"],  # 从配置文件读取轮转间隔
        backupCount=log_config["retention_days"],  # 从配置文件读取保留天数
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # 清理旧日志文件
    cleanup_old_logs(log_dir, log_config["retention_days"])
    
    return logger

def cleanup_old_logs(log_dir: Path, retention_days: int):
    """
    清理超过指定天数的日志文件
    
    Args:
        log_dir: 日志目录路径
        retention_days: 日志保留天数
    """
    current_time = time.time()
    retention_seconds = retention_days * 24 * 60 * 60
    
    for log_file in log_dir.glob("*.log.*"):  # 匹配轮转后的日志文件
        try:
            # 获取文件的最后修改时间
            file_time = os.path.getmtime(log_file)
            if file_time < (current_time - retention_seconds):
                log_file.unlink()  # 删除文件
        except Exception as e:
            print(f"清理日志文件时出错: {e}") 