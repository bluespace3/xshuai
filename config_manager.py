import os
import configparser
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, config_file: str = "model_config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(__file__), self.config_file)
        if os.path.exists(config_path):
            self.config.read(config_path, encoding='utf-8')

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """获取整数配置值"""
        return self.config.getint(section, key, fallback=fallback)

    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """获取浮点数配置值"""
        return self.config.getfloat(section, key, fallback=fallback)

    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """获取布尔配置值"""
        return self.config.getboolean(section, key, fallback=fallback)

    def get_list(self, section: str, key: str, fallback: list = None, separator: str = ',') -> list:
        """获取列表配置值"""
        if fallback is None:
            fallback = []
        value = self.get(section, key)
        if value:
            return [item.strip() for item in value.split(separator) if item.strip()]
        return fallback

    def get_models(self) -> Dict[str, str]:
        """获取模型配置"""
        if 'models' not in self.config:
            return self._get_default_models()
        return {
            'tool': self.config.get('models', 'tool_model', fallback='zdolny/qwen3-coder58k-tools:latest'),
            'text': self.config.get('models', 'text_model', fallback='gpt-oss:20b'),
            'vision': self.config.get('models', 'vision_model', fallback='qwen3-vl:8b'),
            'ocr': self.config.get('models', 'ocr_model', fallback='qwen3-vl:8b')
        }

    def _get_default_models(self) -> Dict[str, str]:
        """获取默认模型配置"""
        return {
            'tool': 'zdolny/qwen3-coder58k-tools:latest',
            'text': 'gpt-oss:20b',
            'vision': 'qwen3-vl:8b',
            'ocr': 'qwen3-vl:8b'
        }

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return {
            'ollama_port': self.get_int('system', 'ollama_port', 11434),
            'ollama_host': self.get('system', 'ollama_host', '127.0.0.1'),
            'log_directory': self.get('system', 'log_directory', 'logs'),
            'temp_directory': self.get('system', 'temp_directory', ''),
            'max_retries': self.get_int('system', 'max_retries', 3),
            'retry_delay': self.get_int('system', 'retry_delay', 2),
            'connection_timeout': self.get_int('system', 'connection_timeout', 5)
        }

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return {
            'max_file_size_mb': self.get_int('security', 'max_file_size_mb', 10),
            'allowed_image_formats': self.get_list('security', 'allowed_image_formats',
                                                 fallback=['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp']),
            'clipboard_timeout_sec': self.get_int('security', 'clipboard_timeout_sec', 5),
            'max_clipboard_retries': self.get_int('security', 'max_clipboard_retries', 3),
            'max_input_length': self.get_int('security', 'max_input_length', 10000),
            'max_filename_length': self.get_int('security', 'max_filename_length', 256)
        }

# 全局配置实例
config = ConfigManager()