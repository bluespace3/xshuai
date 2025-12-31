"""
增强的 LLM 模型实现
专门解决 AgentScope thinking 警告问题
"""
from agentscope.model import OllamaChatModel
from agentscope.message import Msg, TextBlock
import logging

class SilentOllamaChatModel(OllamaChatModel):
    """
    静音处理 thinking 块的 Ollama 模型

    通过重写响应解析逻辑，彻底消除 "Unsupported block type thinking" 警告
    """

    def __init__(self, enable_thinking=False, **kwargs):
        """
        初始化静音模型

        Args:
            enable_thinking: 是否启用 thinking 功能（默认关闭）
            **kwargs: 其他 OllamaChatModel 参数
        """
        # 强制禁用 thinking，避免警告
        super().__init__(enable_thinking=False, **kwargs)

        # 记录模型配置用于调试
        self.model_name = kwargs.get('model_name', 'unknown')
        self.enable_thinking = False

    def _parse_response(self, response: str) -> Msg:
        """
        重写响应解析方法，静默处理 thinking 块

        Args:
            response: Ollama API 原始响应

        Returns:
            解析后的消息对象
        """
        try:
            # 调用父类方法进行基础解析
            msg = super()._parse_response(response)

            # 如果解析成功，检查并处理 thinking 内容
            if hasattr(msg, 'content') and msg.content:
                processed_content = []

                for block in msg.content:
                    if isinstance(block, dict):
                        block_type = block.get('type', '')

                        # 将 thinking 块转换为普通文本块，避免警告
                        if block_type == 'thinking':
                            thinking_content = block.get('thinking', '')
                            if thinking_content:
                                # 将 thinking 内容附加到下一个文本块，或者创建新的文本块
                                processed_content.append(TextBlock(
                                    type="text",
                                    text=thinking_content
                                ))
                        else:
                            # 保留其他类型的块
                            processed_content.append(block)
                    else:
                        processed_content.append(block)

                # 更新消息内容
                msg.content = processed_content

            return msg

        except Exception as e:
            # 如果解析失败，记录错误但不抛出异常
            logging.warning(f"SilentOllamaChatModel 解析响应时出错: {e}")
            # 返回基础解析结果
            return super()._parse_response(response)

    def _merge_thinking_silently(self, result):
        """
        静默合并 thinking 内容

        这个方法用于在解析过程中将 thinking 内容合并到文本中，
        避免产生不支持的块类型警告。
        """
        if hasattr(result, 'content') and result.content:
            merged_content = []
            thinking_buffer = ""

            for block in result.content:
                if isinstance(block, dict):
                    if block.get('type') == 'thinking':
                        # 收集 thinking 内容
                        thinking_buffer += block.get('thinking', '') + "\n"
                    elif block.get('type') == 'text':
                        # 将 thinking 内容附加到文本块之前
                        text_content = block.get('text', '')
                        if thinking_buffer:
                            text_content = thinking_buffer.strip() + "\n\n" + text_content
                            thinking_buffer = ""
                        merged_content.append(TextBlock(
                            type="text",
                            text=text_content
                        ))
                    else:
                        merged_content.append(block)
                else:
                    merged_content.append(block)

            # 如果还有未处理的 thinking 内容，创建新的文本块
            if thinking_buffer.strip():
                merged_content.append(TextBlock(
                    type="text",
                    text=thinking_buffer.strip()
                ))

            result.content = merged_content

        return result

class EnhancedXXzhouModel:
    """
    增强的 XXzhou 模型管理器
    集成静音模型和性能监控
    """

    def __init__(self):
        # 导入原有的模型配置
        from llm import XXzhouModel
        self.original_model = XXzhouModel()
        self.model_config = self.original_model.model_config

    def get_silent_vision_model(self):
        """
        获取静音的视觉模型

        Returns:
            SilentOllamaChatModel: 配置了静音处理的视觉模型
        """
        return SilentOllamaChatModel(
            model_name=self.model_config['vision_model'],
            stream=True,
            options={
                "temperature": 0.5,
                "top_p": 0.9,
                "num_predict": 1024
            }
        )

    def get_silent_text_model(self):
        """
        获取静音的文本模型

        Returns:
            SilentOllamaChatModel: 配置了静音处理的文本模型
        """
        return SilentOllamaChatModel(
            model_name=self.model_config['text_model'],
            stream=True,
            options={
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024
            }
        )

    def get_silent_tool_calling_model(self):
        """
        获取静音的工具调用模型

        Returns:
            SilentOllamaChatModel: 配置了静音处理的工具调用模型
        """
        return SilentOllamaChatModel(
            model_name=self.model_config['tool_model'],
            stream=True,
            options={
                "temperature": 0.3,
                "top_p": 0.9,
                "num_predict": 512
            }
        )

    def get_ocr_model(self):
        """
        获取专用的 OCR 模型（优化参数配置）

        Returns:
            SilentOllamaChatModel: 专门用于 OCR 的模型
        """
        return SilentOllamaChatModel(
            model_name=self.model_config.get('ocr_model', self.model_config['vision_model']),
            stream=True,
            options={
                "temperature": 0.1,  # OCR 需要更高的确定性
                "top_p": 0.8,      # 降低随机性
                "num_predict": 512,  # OCR 输出通常较短
                "repeat_penalty": 1.1  # 避免重复
            }
        )