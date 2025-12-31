from agentscope.message import TextBlock
from agentscope.tool import ToolResponse
from pathlib import Path

def create_images(prompt:str, images:list, save_dir:str):
    """
    图像生成工具（当前版本暂不支持）

    :param prompt: 用户的提示词
    :type prompt: str
    :param images: 本地图片的访问路径组成的列表
    :type images: list
    :save_dir: 生成图片保存的位置
    :type save_dir: str
    """

    print('----图像生成功能----')

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text="""
🚫 图像生成功能暂不可用

当前项目已切换到本地Ollama模型，但Ollama本身不支持图像生成。

如需图像生成功能，您可以：

1. **继续使用阿里云DashScope服务**：
   - 配置QWEN_API_KEY环境变量
   - 恢复create_image.py中的DashScope API调用

2. **使用其他图像生成服务**：
   - Stable Diffusion WebUI
   - ComfyUI
   - DALL-E API
   - Midjourney API

3. **等待Ollama支持图像生成**：
   - 关注Ollama未来版本更新

当前可用的功能：
- ✅ 图像识别和内容分析
- ✅ 文本对话和问答
- ✅ 视频下载
""",
            ),
        ]
    )

