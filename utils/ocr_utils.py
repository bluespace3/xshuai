"""
OCR 工具函数
提供文字识别相关的辅助功能
"""
import os
import tempfile
from PIL import Image
from agentscope.message import Msg, TextBlock, ImageBlock, Base64Source
from agentscope.tool import ToolResponse
from agents.ocr_agent import ocr_agent
import asyncio

async def ocr_image(prompt: str, image_path: str):
    """
    专用OCR文字识别工具

    Args:
        prompt: 用户的提示词（会被优化为OCR专用）
        image_path: 图片文件路径

    Returns:
        ToolResponse: 识别的文字内容
    """
    # 验证图片文件
    if not os.path.exists(image_path):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误: 图片文件不存在: {image_path}"
                )
            ]
        )

    # 检查文件大小
    file_size = os.path.getsize(image_path)
    if file_size == 0:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"错误: 图片文件为空: {image_path}"
                )
            ]
        )

    # 优化提示词为OCR专用
    ocr_prompt = f"请识别图片中的文字内容。{prompt}" if prompt.strip() else "请识别图片中的所有文字内容。"

    # 创建消息
    msg = Msg(
        name="user",
        role="user",
        content=[
            TextBlock(
                type="text",
                text=ocr_prompt
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

    try:
        # 调用OCR代理
        result = await ocr_agent(msg)

        # 提取纯文本结果
        if hasattr(result, 'content') and result.content:
            for block in result.content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_result = block.get('text', '').strip()
                    if text_result:
                        return ToolResponse(
                            content=[
                                TextBlock(
                                    type="text",
                                    text=text_result
                                )
                            ]
                        )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="OCR识别完成，但未提取到文字内容"
                )
            ]
        )

    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"OCR识别过程中出现错误: {str(e)}"
                )
            ]
        )

def preprocess_image_for_ocr(image_path: str) -> str:
    """
    为OCR预处理图片

    Args:
        image_path: 原始图片路径

    Returns:
        str: 预处理后的图片路径
    """
    try:
        img = Image.open(image_path)

        # 预处理步骤
        # 1. 转换为RGB模式（如果不是）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 2. 可选：调整大小以提高识别速度
        max_size = 2048
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 3. 可选：增强对比度
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

        # 保存预处理后的图片
        temp_dir = tempfile.gettempdir()
        processed_path = os.path.join(temp_dir, f"ocr_processed_{os.path.basename(image_path)}")
        img.save(processed_path, 'PNG')

        return processed_path

    except Exception as e:
        print(f"图片预处理失败，使用原图: {e}")
        return image_path

def format_ocr_result(text: str, preserve_formatting: bool = True) -> str:
    """
    格式化OCR结果

    Args:
        text: 原始识别文本
        preserve_formatting: 是否保持原始格式

    Returns:
        str: 格式化后的文本
    """
    if not preserve_formatting:
        # 简单清理：去除多余空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    # 保持格式：只清理明显的错误
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # 保留有意义的内容行
        if line.strip() or any(c.strip() for c in line):
            cleaned_lines.append(line.rstrip())

    return '\n'.join(cleaned_lines)

def detect_text_heuristic(text: str) -> bool:
    """
    检测文本是否为有意义的内容

    Args:
        text: 待检测的文本

    Returns:
        bool: 是否有意义的内容
    """
    if not text or not text.strip():
        return False

    # 检查是否包含文字字符（而非随机字符）
    import re
    text_chars = re.findall(r'[a-zA-Z\u4e00-\u9fff]', text)

    # 如果文字字符少于总数的10%，可能不是有意义的内容
    total_chars = len(re.findall(r'[^\s]', text))
    if total_chars > 0 and len(text_chars) / total_chars < 0.1:
        return False

    # 检查是否有重复的单字符（可能是OCR错误）
    single_chars = [char for char in text.strip() if len(char) == 1 and not char.isspace()]
    if len(set(single_chars)) < 3 and len(single_chars) > 5:
        return False

    return True