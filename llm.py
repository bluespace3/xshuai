import os
from dotenv import load_dotenv
from agentscope.model import OllamaChatModel
from configparser import ConfigParser

# 导入增强的静音模型
try:
    from llm_enhanced import SilentOllamaChatModel, EnhancedXXzhouModel
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False
    print("[警告] 无法导入增强模型，使用原始实现")

load_dotenv()

class XXzhouModel():
    def __init__(self):
        # Ollama不需要API密钥，使用本地模型
        self.model_config = self._load_model_config()

    def _load_model_config(self):
        """从配置文件加载模型配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'model_config.ini')

        if not os.path.exists(config_path):
            # 如果配置文件不存在，使用默认配置
            print(f"[警告] 配置文件 {config_path} 不存在，使用默认配置")
            return {
                'tool_model': 'zdolny/qwen3-coder58k-tools:latest',
                'text_model': 'gpt-oss:20b',
                'vision_model': 'gemma3:27b'
            }

        config = ConfigParser()
        config.read(config_path, encoding='utf-8')

        if 'models' not in config:
            print("[警告] 配置文件缺少 [models] 部分，使用默认配置")
            return {
                'tool_model': 'zdolny/qwen3-coder58k-tools:latest',
                'text_model': 'gpt-oss:20b',
                'vision_model': 'gemma3:27b'
            }

        models_config = config['models']
        return {
            'tool_model': models_config.get('tool_model', 'zdolny/qwen3-coder58k-tools:latest'),
            'text_model': models_config.get('text_model', 'gpt-oss:20b'),
            'vision_model': models_config.get('vision_model', 'gemma3:27b')
        }

    def get_tool_calling_model(self):
        """获取专门用于工具调用的模型"""
        return OllamaChatModel(
            model_name=self.model_config['tool_model'],
            stream=True,
            options={
                "temperature": 0.3,  # 工具调用需要更确定性
                "top_p": 0.9,
                "num_predict": 512   # 工具调用通常不需要太长输出
            }
        )

    def get_general_text_model(self):
        """获取通用文本生成模型"""
        return OllamaChatModel(
            model_name=self.model_config['text_model'],
            stream=True,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024
            }
        )

    def get_vision_model(self):
        """获取视觉识别模型"""
        if ENHANCED_MODE:
            # 使用静音模型，彻底解决 thinking 警告
            return SilentOllamaChatModel(
                model_name=self.model_config['vision_model'],
                stream=True,
                options={
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "num_predict": 1024
                }
            )
        else:
            # 回退到原始实现（保留现有的stop参数）
            return OllamaChatModel(
                model_name=self.model_config['vision_model'],
                stream=True,
                options={
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "num_predict": 1024,
                    # 禁用thinking模式以避免警告
                    "stop": ["<thinking>", "</thinking>"]
                }
            )
