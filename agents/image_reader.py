from agentscope.agent import ReActAgent
from agentscope.formatter import OllamaChatFormatter

# 使用增强模型管理器获取静音视觉模型
try:
    from llm_enhanced import EnhancedXXzhouModel
    enhanced_model = EnhancedXXzhouModel()
    vision_model = enhanced_model.get_silent_vision_model()
except ImportError:
    # 回退到原始实现
    from llm import XXzhouModel
    vision_model = XXzhouModel().get_vision_model()

image_reader_agent = ReActAgent(
    name="image reader",
    sys_prompt="你可以识别图片上的内容，并用语言描述图片内容。",
    formatter=OllamaChatFormatter(),  # 使用标准formatter， SilentOllamaChatModel会处理thinking块
    toolkit=[],
    model=vision_model
)

# 禁用控制台输出，避免thinking内容显示给用户
image_reader_agent.set_console_output_enabled(False)


