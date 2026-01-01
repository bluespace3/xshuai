import os
from dotenv import load_dotenv
from agentscope.model import OllamaChatModel
from config_manager import config

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
        self.model_config = config.get_models()

    def get_tool_calling_model(self):
        """获取专门用于工具调用的模型"""
        return OllamaChatModel(
            model_name=self.model_config['tool'],
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
            model_name=self.model_config['text'],
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
                model_name=self.model_config['vision'],
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
                model_name=self.model_config['vision'],
                stream=True,
                options={
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "num_predict": 1024,
                    # 禁用thinking模式以避免警告
                    "stop": ["<thinking>", "</thinking>"]
                }
            )
