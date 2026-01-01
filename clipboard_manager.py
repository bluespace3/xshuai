import os
import time
import tempfile
from typing import Optional, List, Any
import win32clipboard
from PIL import Image, ImageGrab
import io
from config_manager import config
from decorators import safe_execute, retry_on_failure

class ClipboardManager:
    """剪贴板操作管理器"""

    def __init__(self):
        security_config = config.get_security_config()
        self.max_retries = security_config['max_clipboard_retries']
        self.retry_delay = security_config['clipboard_timeout_sec'] / self.max_retries
        self.allowed_formats = security_config['allowed_image_formats']

    @safe_execute(default_return=False)
    def _open_clipboard(self) -> bool:
        """安全打开剪贴板"""
        for attempt in range(self.max_retries):
            try:
                win32clipboard.OpenClipboard()
                return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
        return False

    def _close_clipboard(self):
        """安全关闭剪贴板"""
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass

    @safe_execute(default_return=[])
    def _get_clipboard_formats(self) -> List[int]:
        """获取剪贴板可用格式"""
        formats = []
        try:
            fmt = 0
            while True:
                fmt = win32clipboard.EnumClipboardFormats(fmt)
                if fmt == 0:
                    break
                formats.append(fmt)
        except Exception:
            pass
        return formats

    @safe_execute(default_return="")
    def get_text_content(self) -> str:
        """获取剪贴板文本内容"""
        if not self._open_clipboard():
            return ""

        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            return ""
        finally:
            self._close_clipboard()

    @safe_execute(default_return="")
    def get_image_path(self) -> str:
        """获取剪贴板图片路径"""
        # 首先尝试PIL ImageGrab
        if ImageGrab:
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    return self._save_temp_image(img)
                elif isinstance(img, list) and len(img) > 0:
                    # 处理文件列表
                    first_file = img[0]
                    if os.path.isfile(first_file) and self._is_allowed_image_format(first_file):
                        return first_file
            except Exception:
                pass

        # 回退到win32clipboard
        return self._save_image_from_clipboard()

    def _is_allowed_image_format(self, file_path: str) -> bool:
        """检查是否为允许的图片格式"""
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext in self.allowed_formats

    @safe_execute(default_return="")
    def _save_temp_image(self, img: Image.Image) -> str:
        """保存临时图片文件"""
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"clipboard_image_{os.getpid()}.png")
        img.save(temp_path, 'PNG')
        return temp_path

    @safe_execute(default_return="")
    def _save_image_from_clipboard(self) -> str:
        """从剪贴板保存图片到临时文件"""
        if not self._open_clipboard():
            return ""

        try:
            image_formats = [
                win32clipboard.CF_DIB,
                win32clipboard.CF_BITMAP,
                win32clipboard.CF_ENHMETAFILE,
            ]

            for fmt in image_formats:
                if win32clipboard.IsClipboardFormatAvailable(fmt):
                    try:
                        data = win32clipboard.GetClipboardData(fmt)
                        if data:
                            result = self._process_image_data(data, fmt)
                            if result:
                                return result
                    except Exception:
                        continue
            return ""
        finally:
            self._close_clipboard()

    @safe_execute(default_return="")
    def _process_image_data(self, data: bytes, format_type: int) -> str:
        """处理图片数据并保存到文件"""
        try:
            # 处理DIB格式
            if format_type == win32clipboard.CF_DIB:
                return self._process_dib_data(data)

            # 处理其他格式
            return self._process_generic_image_data(data)
        except Exception:
            return ""

    def _process_dib_data(self, data: bytes) -> str:
        """处理DIB格式数据"""
        try:
            # 创建BMP文件头
            bmp_header = b'BM'
            file_size = len(data) + 14
            bmp_header += file_size.to_bytes(4, 'little')
            bmp_header += b'\x00\x00'  # Reserved
            bmp_header += b'\x00\x00'  # Reserved
            bmp_header += (54).to_bytes(4, 'little')  # Offset to pixel data

            # 创建完整的BMP数据
            bmp_data = bmp_header + data

            # 使用PIL读取BMP数据
            img = Image.open(io.BytesIO(bmp_data))
            return self._save_temp_image(img)
        except Exception:
            return ""

    def _process_generic_image_data(self, data: bytes) -> str:
        """处理通用图片数据"""
        try:
            if isinstance(data, bytes):
                img = Image.open(io.BytesIO(data))
                return self._save_temp_image(img)
        except Exception:
            return ""

    @retry_on_failure(max_retries=3, delay=0.2)
    def get_clipboard_content(self) -> str:
        """获取剪贴板内容（文本或图片路径）"""
        # 首先尝试获取文本
        text_content = self.get_text_content()
        if text_content and text_content.strip():
            return text_content

        # 然后尝试获取图片
        image_path = self.get_image_path()
        if image_path:
            return image_path

        return ""

# 全局剪贴板管理器实例
clipboard_manager = ClipboardManager()