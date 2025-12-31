import re
import os
from typing import Optional
from agentscope.agent import ReActAgent
from agentscope.formatter import OllamaChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit
from agentscope.message import Msg
from configparser import ConfigParser

from llm import XXzhouModel
from tools.download_video import download_video
from tools.create_image import create_images
from tools.image_reader import images_reader

class SmartAgent:
    """智能Agent，根据用户输入自动选择最适合的模型"""

    def __init__(self):
        self.model_manager = XXzhouModel()

        # 从配置文件加载模型配置
        self.model_names = self._load_model_config()

        # 初始化工具套件
        self.toolkit = Toolkit()
        self.toolkit.register_tool_function(download_video)
        self.toolkit.register_tool_function(create_images)
        self.toolkit.register_tool_function(images_reader)

        # 导入OCR工具
        from utils.ocr_utils import ocr_image
        self.toolkit.register_tool_function(ocr_image)

        # 创建不同场景的Agent
        self.tool_agent = ReActAgent(
            name="小帅工具助手",
            sys_prompt="""
            1. 你可以使用download_video工具下载视频。
            2. 你根据用户的prompt，调用create_images工具生成图片。
            3. 使用images_reader识别图片内容。

            请专注于调用合适的工具来完成用户的任务。
            """,
            formatter=OllamaChatFormatter(),
            toolkit=self.toolkit,
            memory=InMemoryMemory(),
            model=self.model_manager.get_tool_calling_model()
        )
        self.tool_agent.set_console_output_enabled(False)

        self.text_agent = ReActAgent(
            name="小帅对话助手",
            sys_prompt="""
            你是一个智能助手，专注于对话和文本处理。
            请用自然、友好的方式回答用户的问题。
            """,
            formatter=OllamaChatFormatter(),
            toolkit=[],  # 不使用工具
            memory=InMemoryMemory(),
            model=self.model_manager.get_general_text_model()
        )
        self.text_agent.set_console_output_enabled(False)

        # 为视觉agent创建独立的toolkit
        vision_toolkit = Toolkit()
        vision_toolkit.register_tool_function(images_reader)

        # 从llm_enhanced导入增强模型管理器用于视觉模型
        try:
            from llm_enhanced import EnhancedXXzhouModel
            enhanced_model = EnhancedXXzhouModel()
            self.vision_model = enhanced_model.get_silent_vision_model()
        except ImportError:
            self.vision_model = self.model_manager.get_vision_model()

        self.vision_agent = ReActAgent(
            name="小帅视觉助手",
            sys_prompt="""
你是一个专业的图片识别助手。当用户提供图片路径或图片相关请求时，你必须：

1. 使用 images_reader 工具来识别和分析图片内容
2. 根据用户的具体问题，调用 images_reader(prompt, image_dir) 工具
3. 其中 prompt 是用户的问题，image_dir 是图片的文件路径
4. 然后根据工具返回的结果，详细回答用户的问题

重要：不要解释文件路径或文件格式，而是要实际调用工具来分析图片内容！
""",
            formatter=OllamaChatFormatter(),
            toolkit=vision_toolkit,  # 只保留图像识别功能
            memory=InMemoryMemory(),
            model=self.vision_model
        )
        self.vision_agent.set_console_output_enabled(False)

        # 创建OCR专用的toolkit
        ocr_toolkit = Toolkit()
        ocr_toolkit.register_tool_function(ocr_image)

        # 从llm_enhanced导入增强模型管理器
        try:
            from llm_enhanced import EnhancedXXzhouModel
            enhanced_model = EnhancedXXzhouModel()
            self.ocr_model = enhanced_model.get_ocr_model()
        except ImportError:
            self.ocr_model = self.model_manager.get_vision_model()

        self.ocr_agent = ReActAgent(
            name="小帅OCR助手",
            sys_prompt="""你是一个专业的OCR（文字识别）助手。当用户提供图片时，你必须：

1. 使用 ocr_image 工具来识别图片中的文字内容
2. 调用 ocr_image(prompt, image_path) 工具，其中 prompt 是识别要求，image_path 是图片路径
3. 直接返回识别的文字内容，不添加额外分析或解读
4. 如果没有明确要求，就识别所有可见文字

重要：专注于文字提取，不要进行图片内容分析或解读！""",
            formatter=OllamaChatFormatter(),
            toolkit=ocr_toolkit,
            memory=InMemoryMemory(),
            model=self.ocr_model
        )
        self.ocr_agent.set_console_output_enabled(False)

    def _load_model_config(self):
        """从配置文件加载模型配置"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'model_config.ini')

        if not os.path.exists(config_path):
            # 如果配置文件不存在，使用默认配置
            print(f"[警告] 配置文件 {config_path} 不存在，使用默认配置")
            return {
                'tool': 'zdolny/qwen3-coder58k-tools:latest',
                'text': 'gpt-oss:20b',
                'vision': 'gemma3:27b'
            }

        config = ConfigParser()
        config.read(config_path, encoding='utf-8')

        if 'models' not in config:
            print("[警告] 配置文件缺少 [models] 部分，使用默认配置")
            return {
                'tool': 'zdolny/qwen3-coder58k-tools:latest',
                'text': 'gpt-oss:20b',
                'vision': 'gemma3:27b'
            }

        models_config = config['models']
        return {
            'tool': models_config.get('tool_model', 'zdolny/qwen3-coder58k-tools:latest'),
            'text': models_config.get('text_model', 'gpt-oss:20b'),
            'vision': models_config.get('vision_model', 'qwen3-vl:8b'),
            'ocr': models_config.get('ocr_model', 'qwen3-vl:8b')  # OCR使用专用模型配置
        }

    def _detect_scenario(self, user_input: str) -> str:
        """检测用户输入的场景类型"""
        user_input = user_input.lower()

        # 检测是否为OCR专用命令
        ocr_patterns = [
            r'^ocr\s', r'文字识别', r'文本识别', r'提取文字',
            r'识别.*文字', r'图片.*文字', r'截图.*文字',
            r'文档.*识别', r'表格.*识别'
        ]

        for pattern in ocr_patterns:
            if re.search(pattern, user_input):
                return 'ocr'

        # 检测是否需要图像识别
        image_patterns = [
            r'图片.*内容', r'图片.*是什么', r'图片.*描述',
            r'图片.*识别', r'.*\.png', r'.*\.jpg', r'.*\.jpeg',
            r'.*\.gif', r'.*\.webp', r'图像.*内容', r'照片.*内容'
        ]

        for pattern in image_patterns:
            if re.search(pattern, user_input):
                return 'vision'

        # 检测是否需要工具调用
        tool_patterns = [
            r'下载.*视频', r'生成.*图片', r'创建.*图片', r'图片.*生成',
            r'下载.*音乐', r'下载.*文件', r'图片.*处理', r'给.*图片.*',
            r'下载.*http', r'下载.*www', r'下载.*url'
        ]

        for pattern in tool_patterns:
            if re.search(pattern, user_input):
                return 'tool'

        # 检测是否包含文件路径（可能是图像相关）
        file_patterns = [
            r'[a-zA-Z]:\\[^\\]+\\[^\\]+\\[^\\]+\.(png|jpg|jpeg|gif|webp)',
            r'[^\\]+\.(png|jpg|jpeg|gif|webp)'
        ]

        for pattern in file_patterns:
            if re.search(pattern, user_input):
                return 'vision'

        # 默认为文本对话
        return 'text'

    async def __call__(self, msg: Msg) -> any:
        """根据用户输入自动选择合适的Agent处理请求"""
        user_input = msg.content if isinstance(msg.content, str) else str(msg.content)

        # 检测场景
        scenario = self._detect_scenario(user_input)

        print(f"[系统] 检测到场景类型: {scenario}")
        print(f"[系统] 当前使用模型: {self.model_names[scenario]}")

        # 选择对应的Agent，添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if scenario == 'ocr':
                    return await self.ocr_agent(msg)
                elif scenario == 'vision':
                    return await self.vision_agent(msg)
                elif scenario == 'tool':
                    return await self.tool_agent(msg)
                else:
                    return await self.text_agent(msg)
            except Exception as e:
                # 更详细的错误信息
                error_type = type(e).__name__
                error_msg = str(e)
                if attempt < max_retries - 1:
                    print(f"[系统] 第{attempt + 1}次尝试失败，正在重试...")
                    print(f"[系统] 错误类型: {error_type}")
                    print(f"[系统] 错误详情: {error_msg}")
                    import asyncio
                    await asyncio.sleep(2)  # 等待2秒后重试
                else:
                    print(f"[系统] 所有重试均失败")
                    print(f"[系统] 错误类型: {error_type}")
                    print(f"[系统] 错误详情: {error_msg}")
                    # 返回一个友好的错误消息
                    from agentscope.message import TextBlock
                    msg.content = [
                        TextBlock(
                            type="text",
                            text=f"抱歉，处理请求时遇到问题：{error_msg}\n\n建议：\n1. 检查Ollama服务是否正常运行\n2. 等待片刻后重试\n3. 尝试重启Ollama服务"
                        )
                    ]
                    return msg

# 创建智能Agent实例
smart_agent = SmartAgent()
agent = smart_agent  # 为了兼容现有代码