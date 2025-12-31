from agentscope.tool import ToolResponse
from agentscope.message import (
    Msg, 
    TextBlock,
    ImageBlock,
    Base64Source
)
from agents.image_reader import image_reader_agent
import asyncio

async def images_reader(prompt:str, image_dir:str):
    """
    根据用户的提示词，识别并分析图片的内容
    :param prompt: 用户的提示词
    :param image_dir: 图片的本地位置（可以是文件路径或目录路径）
    """
    import os
    import re

    # 如果image_dir是目录，尝试找到其中的图片文件
    if os.path.isdir(image_dir):
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
        image_files = []

        for file in os.listdir(image_dir):
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_files.append(os.path.join(image_dir, file))

        if not image_files:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"在目录 {image_dir} 中未找到图片文件。支持的格式：{', '.join(image_extensions)}"
                    )
                ]
            )

        # 使用找到的第一个图片文件
        image_path = image_files[0]

    elif os.path.isfile(image_dir):
        image_path = image_dir
    else:
        # 尝试从提示词中提取文件名
        import re
        file_pattern = r'(\w+\.(png|jpg|jpeg|gif|webp|bmp))'
        match = re.search(file_pattern, prompt, re.IGNORECASE)
        if match:
            filename = match.group(1)
            # 在当前目录查找
            current_dir = os.getcwd()
            potential_path = os.path.join(current_dir, filename)
            if os.path.exists(potential_path):
                image_path = potential_path
            else:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"无法找到图片文件: {filename}。请确认文件路径。"
                        )
                    ]
                )
        else:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"无法找到图片文件: {image_dir}。请确认文件路径。"
                    )
                ]
            )

    msg = Msg(
        name="user",
        role="user",
        content=[
            TextBlock(
                type="text",
                text=prompt
            ),
            ImageBlock(
                type="image",
                source=Base64Source(
                    type="url",
                    url=image_path
                )
            )
        ]
    )

    # Debug: verify the image file exists and is accessible
    if os.path.exists(image_path):
        file_size = os.path.getsize(image_path)
    else:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误: 图片文件不存在或无法访问: {image_path}"
                )
            ]
        )

    try:
        res = await image_reader_agent(msg)

        # 更安全地提取结果，只提取text类型的块，忽略thinking块
        text_result = "图像识别完成，但无法提取结果文本"
        if hasattr(res, 'content') and res.content:
            for block in res.content:
                if isinstance(block, dict):
                    if block.get('type') == 'text' and 'text' in block:
                        text_result = block['text']
                        break
                    elif 'text' in block and block.get('type') != 'thinking':
                        # 备用提取方式
                        text_result = block['text']
                        break
                else:
                    # 如果不是字典，转换为字符串（但通常不会发生）
                    text_result = str(block)
        else:
            text_result = "图像识别完成，但无法提取结果文本"

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=text_result
                )
            ]
        )
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"图像识别过程中出现错误: {str(e)}"
                )
            ]
        )

