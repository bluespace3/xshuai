"""
OCR 专用 Agent
专门用于图片文字识别，不添加解读和分析
"""
from agentscope.agent import ReActAgent
from agentscope.formatter import OllamaChatFormatter
from agentscope.memory import InMemoryMemory
from llm_enhanced import SilentOllamaChatModel

class OCRAgent:
    """OCR 专用代理，专注于纯文字提取"""

    def __init__(self):
        # 从 llm_enhanced 导入增强模型管理器
        from llm_enhanced import EnhancedXXzhouModel
        enhanced_model = EnhancedXXzhouModel()

        # 使用 OCR 优化的静音模型
        self.agent = ReActAgent(
            name="OCR识别助手",
            sys_prompt="""你是一个专业的OCR（文字识别）助手。请专注于：

1. 准确识别并提取图片中的所有文字内容
2. 保持原文的格式、换行和段落结构
3. 如果是表格，请保持表格结构
4. 如果是多语言内容，请保持原有语言
5. 只输出识别的文字，不添加任何额外描述、分析或解读

重要约束：
- 不要解释图片内容
- 不要分析图片含义
- 不要添加任何评论或建议
- 只输出原始文字内容""",
            formatter=OllamaChatFormatter(),
            toolkit=[],  # OCR不需要工具
            memory=InMemoryMemory(),
            model=enhanced_model.get_ocr_model()
        )

        # 确保控制台输出被禁用
        self.agent.set_console_output_enabled(False)

    async def __call__(self, msg):
        """
        处理OCR请求

        Args:
            msg: 包含图片的消息

        Returns:
            识别结果消息
        """
        return await self.agent(msg)

# 创建全局实例
ocr_agent = OCRAgent()