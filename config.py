import os
from typing import List, Dict, Any
import yaml

def load_config() -> Dict[str, Any]:
    """加载配置"""
    config = {
        "comfyfile_instances": [],
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0
        }
    }
    
    # 从配置文件读取
    config_file = "config.yaml"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    return config

def save_config(config: Dict[str, Any]):
    """保存配置到文件"""
    config_file = "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f) 