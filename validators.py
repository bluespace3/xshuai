import os
import re
from typing import Optional, List
from config_manager import config

class ValidationError(Exception):
    """验证错误异常"""
    pass

def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> str:
    """验证文件路径安全性"""
    if not file_path or not isinstance(file_path, str):
        raise ValidationError("文件路径不能为空")

    # 规范化路径
    normalized_path = os.path.normpath(file_path)

    # 检查路径遍历
    if '..' in normalized_path or normalized_path.startswith('..'):
        raise ValidationError("检测到路径遍历攻击")

    # 检查绝对路径的安全性
    if os.path.isabs(normalized_path):
        # 确保路径在合理的范围内
        if len(normalized_path) > 260:  # Windows路径长度限制
            raise ValidationError("文件路径过长")

    # 检查扩展名
    if allowed_extensions:
        ext = os.path.splitext(normalized_path)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            raise ValidationError(f"不支持的文件扩展名: {ext}")

    return normalized_path

def validate_user_input(input_text: str, max_length: Optional[int] = None) -> str:
    """验证用户输入"""
    if not isinstance(input_text, str):
        raise ValidationError("输入必须是文本")

    if not input_text or not input_text.strip():
        raise ValidationError("输入不能为空")

    security_config = config.get_security_config()
    if max_length is None:
        max_length = security_config['max_input_length']

    if len(input_text) > max_length:
        raise ValidationError(f"输入长度超过限制 ({max_length} 字符)")

    # 检查恶意字符模式
    dangerous_patterns = [
        r'<script.*?>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
        r'system\s*\('
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, input_text, re.IGNORECASE):
            raise ValidationError("输入包含潜在恶意内容")

    return input_text.strip()

def validate_image_file(file_path: str) -> str:
    """验证图片文件"""
    security_config = config.get_security_config()
    allowed_formats = security_config['allowed_image_formats']
    max_file_size = security_config['max_file_size_mb'] * 1024 * 1024  # 转换为字节

    # 验证文件路径
    validated_path = validate_file_path(file_path, allowed_formats)

    # 检查文件是否存在
    if not os.path.exists(validated_path):
        raise ValidationError(f"文件不存在: {validated_path}")

    # 检查文件大小
    try:
        file_size = os.path.getsize(validated_path)
        if file_size > max_file_size:
            raise ValidationError(f"文件大小超过限制 ({security_config['max_file_size_mb']}MB)")
    except OSError as e:
        raise ValidationError(f"无法读取文件信息: {e}")

    # 尝试验证文件格式
    try:
        from PIL import Image
        with Image.open(validated_path) as img:
            img.verify()  # 验证图片完整性
    except ImportError:
        # 如果PIL不可用，跳过图片验证
        pass
    except Exception as e:
        raise ValidationError(f"图片文件损坏或格式不支持: {e}")

    return validated_path

def validate_filename(filename: str) -> str:
    """验证文件名"""
    if not filename or not isinstance(filename, str):
        raise ValidationError("文件名不能为空")

    security_config = config.get_security_config()
    max_length = security_config['max_filename_length']

    if len(filename) > max_length:
        raise ValidationError(f"文件名过长，最大长度: {max_length}")

    # 检查非法字符
    illegal_chars = '<>:"/\\|?*'
    if any(char in filename for char in illegal_chars):
        raise ValidationError(f"文件名包含非法字符: {illegal_chars}")

    # 检查保留名称（Windows）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        raise ValidationError(f"文件名使用了保留名称: {name_without_ext}")

    return filename