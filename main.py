import sys,asyncio,os
import warnings
import logging
from agents.agent import agent
from agentscope.message import Msg
from ollama import Client

# 设置环境变量来抑制警告
os.environ['PYTHONWARNINGS'] = 'ignore'

# 抑制所有警告，包括thinking警告
warnings.filterwarnings("ignore")

# 配置根logger级别为ERROR，抑制WARNING级别
logging.basicConfig(level=logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

# 尝试导入PIL ImageGrab for better clipboard handling
try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

# Set UTF-8 encoding for stdout to handle Unicode properly
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # For older Python versions or when reconfigure is not available
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 完全重写stderr来过滤thinking警告
class FilteredStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr

    def write(self, text):
        # 过滤掉thinking警告
        if "Unsupported block type thinking" in text:
            return
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)

# 应用stderr过滤器
sys.stderr = FilteredStderr(sys.stderr)

# 如果过滤器还不能完全抑制警告，尝试更激进的方法
import os
if os.name == 'nt':  # Windows
    import subprocess
    subprocess.Popen('', shell=True)  # 防止stderr被完全关闭

def safe_print(text, end='\n', flush=True):
    """Safely print text to console with UTF-8 encoding"""
    try:
        print(text, end=end, flush=flush)
    except UnicodeEncodeError:
        # Fallback: remove problematic characters
        cleaned_text = ''.join(char for char in text if ord(char) < 65536)
        print(cleaned_text, end=end, flush=flush)

def is_ollama_running():
    """检查Ollama服务是否正在运行"""
    try:
        import subprocess
        result = subprocess.run(['ollama', 'ps'], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False

def ensure_ollama_running():
    """确保Ollama服务正在运行，如果未运行则启动它"""
    # 首先检查Ollama是否已经在运行
    if is_ollama_running():
        return True

    # 检查ollama命令是否存在
    try:
        import subprocess
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            safe_print("错误: 未找到Ollama命令。请确保已安装Ollama。")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        safe_print("错误: 未找到Ollama命令。请确保已安装Ollama。")
        return False

    # 启动Ollama服务
    try:
        safe_print("检测到Ollama服务未运行，正在启动...")
        import subprocess
        # 在后台启动Ollama服务
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 主动轮询检查服务是否启动成功（最多30秒）
        import time
        max_wait_time = 30
        check_interval = 2
        elapsed_time = 0

        while elapsed_time < max_wait_time:
            if is_ollama_running():
                safe_print("Ollama服务已成功启动！")
                return True
            time.sleep(check_interval)
            elapsed_time += check_interval
            if elapsed_time % 10 == 0:  # 每10秒提示一次
                safe_print(f"Ollama服务仍在启动中... ({elapsed_time}s)")

        safe_print("警告: Ollama服务启动超时，请手动检查。")
        return False

    except Exception as e:
        safe_print(f"启动Ollama服务时出错: {e}")
        return False

def save_clipboard_image():
    """Save clipboard image to temporary file and return path"""
    import time

    max_attempts = 2  # 最多尝试2次

    for attempt in range(max_attempts):
        try:
            import win32clipboard
            import tempfile
            import os
            from PIL import Image
            import io

            # 预检查：获取剪贴板序列号
            try:
                initial_sequence = win32clipboard.GetClipboardSequenceNumber()
                if attempt > 0:
                    safe_print(f"[剪贴板] 重试 {attempt + 1}/{max_attempts}，序列号: {initial_sequence}")
            except:
                pass

            # First try to get image directly using PIL's clipboard support
            if ImageGrab is not None:
                try:
                    img = ImageGrab.grabclipboard()
                    if img is not None:
                        if isinstance(img, Image.Image):
                            temp_dir = tempfile.gettempdir()
                            temp_image_path = os.path.join(temp_dir, f"clipboard_image_{os.getpid()}.png")
                            img.save(temp_image_path, 'PNG')
                            return temp_image_path
                        elif isinstance(img, list) and len(img) > 0:
                            # Handle case where clipboard contains file paths
                            first_file = img[0]
                            if os.path.isfile(first_file) and any(first_file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
                                return first_file
                    else:
                        # 如果PIL无法读取，可能是剪贴板状态问题，尝试刷新
                        if attempt == 0:
                            # 尝试触发剪贴板刷新
                            for _ in range(2):
                                try:
                                    win32clipboard.OpenClipboard()
                                    win32clipboard.CloseClipboard()
                                    time.sleep(0.1)
                                except:
                                    pass
                except Exception as e:
                    safe_print(f"[剪贴板] PIL ImageGrab失败: {e}")
                    # Fall back to win32clipboard method

            # Fall back to win32clipboard method
            try:
                win32clipboard.OpenClipboard()
            except Exception as e:
                if attempt < max_attempts - 1:
                    safe_print(f"[剪贴板] 无法打开剪贴板，重试中...")
                    time.sleep(0.2)
                    continue
                else:
                    return ""

            try:
                # Check all available formats
                formats = []
                fmt = 0
                while True:
                    fmt = win32clipboard.EnumClipboardFormats(fmt)
                    if fmt == 0:
                        break
                    formats.append(fmt)

                if not formats:
                    if attempt < max_attempts - 1:
                        # 剪贴板为空，等待一下再试
                        win32clipboard.CloseClipboard()
                        time.sleep(0.3)
                        continue
                    else:
                        return ""

                # Try different image formats
                image_formats = [
                    win32clipboard.CF_DIB,
                    win32clipboard.CF_BITMAP,
                    win32clipboard.CF_ENHMETAFILE,
                    49156,  # PNG format
                    49157,  # JPEG format
                    49158,  # GIF format
                    49159,  # TIFF format
                ]

                for fmt in image_formats:
                    if win32clipboard.IsClipboardFormatAvailable(fmt):
                        try:
                            data = win32clipboard.GetClipboardData(fmt)
                            if data:
                                # Create a temporary file to save the image
                                temp_dir = tempfile.gettempdir()
                                temp_image_path = os.path.join(temp_dir, f"clipboard_image_{os.getpid()}.png")

                                # Handle DIB format
                                if fmt == win32clipboard.CF_DIB:
                                    try:
                                        from io import BytesIO

                                        # Create a BMP file in memory from DIB data
                                        bmp_header = b'BM'  # BMP signature

                                        # Calculate file size
                                        file_size = len(data) + 14  # 14 bytes for BMP header
                                        bmp_header += file_size.to_bytes(4, 'little')
                                        bmp_header += b'\x00\x00'  # Reserved
                                        bmp_header += b'\x00\x00'  # Reserved
                                        bmp_header += (54).to_bytes(4, 'little')  # Offset to pixel data

                                        # Create complete BMP data
                                        bmp_data = bmp_header + data

                                        # Use PIL to read the BMP data
                                        img = Image.open(BytesIO(bmp_data))
                                        img.save(temp_image_path, 'PNG')
                                        return temp_image_path

                                    except Exception as e:
                                        continue

                                # Handle other formats - try to save directly
                                else:
                                    try:
                                        # Try to save as image
                                        if isinstance(data, bytes):
                                            img = Image.open(io.BytesIO(data))
                                            img.save(temp_image_path, 'PNG')
                                            return temp_image_path
                                    except Exception as e:
                                        continue

                        except Exception as e:
                            continue

                # If no image formats found or processing failed
                if attempt < max_attempts - 1:
                    # 可能是剪贴板状态问题，尝试强制刷新
                    win32clipboard.CloseClipboard()
                    time.sleep(0.3)
                    continue
                else:
                    return ""

            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass  # Ignore closing errors

        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(0.2)
                continue
            else:
                return ""

    return ""

def get_clipboard_content():
    """Get clipboard content (text or image path) from Windows clipboard"""
    import time

    max_retries = 3
    retry_delay = 0.5  # 0.5秒延迟

    for attempt in range(max_retries):
        try:
            import win32clipboard

            try:
                win32clipboard.OpenClipboard()
            except Exception as e:
                if attempt < max_retries - 1:
                    safe_print(f"无法打开剪贴板，重试中... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    safe_print(f"无法打开剪贴板: {e}")
                    return ""

            try:
                # 检查剪贴板是否为空
                format_count = 0
                try:
                    import win32api
                    format_count = win32clipboard.CountClipboardFormats()
                except:
                    # 如果CountClipboardFormats失败，手动检查
                    fmt = 0
                    while True:
                        fmt = win32clipboard.EnumClipboardFormats(fmt)
                        if fmt == 0:
                            break
                        format_count += 1

                if format_count == 0:
                    if attempt < max_retries - 1:
                        safe_print(f"剪贴板为空，等待内容... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        safe_print("剪贴板为空，请确保已复制内容到剪贴板")
                        return ""

                # First check if there's text in clipboard
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    # Return the full text content (preserve newlines and formatting)
                    if text and text.strip():  # If text is not empty after stripping
                        return text

                # Check for file list (CF_HDROP)
                try:
                    import win32con
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                        import win32api
                        data = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                        file_count = win32api.DragQueryFile(data, -1)
                        if file_count > 0:
                            # 返回第一个文件路径
                            first_file = win32api.DragQueryFile(data, 0)
                            if first_file and any(first_file.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']):
                                return first_file
                except:
                    pass

                # Check for image content
                image_path = save_clipboard_image()
                if image_path:
                    return image_path

                # If no content found, try again
                if attempt < max_retries - 1:
                    safe_print(f"剪贴板中没有识别的内容，重试中... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    safe_print("剪贴板中没有文本或图片内容")
                    return ""

            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass  # Ignore closing errors

        except Exception as e:
            if attempt < max_retries - 1:
                safe_print(f"访问剪贴板出错，重试中... ({attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                continue
            else:
                safe_print(f"Error accessing clipboard: {e}")
                return ""

    return ""

async def stream_response(msg):
    """真正的流式输出响应"""
    try:
        # Get the current working agent
        from agents.smart_agent import smart_agent

        # Extract original user input (without directory info)
        full_content = msg.content if isinstance(msg.content, str) else str(msg.content)
        # Remove the directory suffix to get original user input
        if "当前目录为：" in full_content:
            user_input = full_content.split("当前目录为：")[0].strip()
        else:
            user_input = full_content

        # Detect scenario and get appropriate agent
        scenario = smart_agent._detect_scenario(user_input)

        print(f"[系统] 检测到场景类型: {scenario}")
        print(f"[系统] 当前使用模型: {smart_agent.model_names[scenario]}")

        # For text-only scenarios, use native Ollama streaming
        if scenario == 'text':
            # Get the model name for direct Ollama call
            model_name = smart_agent.model_names[scenario]

            # Prepare messages for Ollama
            messages = [{"role": "user", "content": user_input}]

            # Create Ollama client
            client = Client()

            # Stream the response directly from Ollama
            stream = client.chat(
                model=model_name,
                messages=messages,
                stream=True
            )

            # Process the stream
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    if content:
                        safe_print(content, end='', flush=True)
            print()  # Final newline
        else:
            # For tool/vision scenarios, use AgentScope with better feedback

            # 直接调用相应的agent，避免重复检测场景
            if scenario == 'vision':
                res = await smart_agent.vision_agent(msg)
            elif scenario == 'tool':
                res = await smart_agent.tool_agent(msg)
            else:
                res = await smart_agent.text_agent(msg)

            if res.content and len(res.content) > 0:
                # 只显示文本内容，忽略thinking块
                text_displayed = False
                for content in res.content:
                    if isinstance(content, dict):
                        # 跳过thinking块
                        if content.get('type') == 'thinking':
                            continue
                        elif 'text' in content:
                            safe_print(content['text'])
                            text_displayed = True
                        elif 'content' in content:
                            safe_print(content['content'])
                            text_displayed = True
                        elif content.get('type') == 'text':
                            safe_print(content.get('text', str(content)))
                            text_displayed = True
                        else:
                            # 如果是其他类型但不是thinking，也显示
                            if content.get('type') != 'thinking':
                                safe_print(str(content))
                                text_displayed = True
                    else:
                        # 非字典类型，直接显示
                        safe_print(str(content))
                        text_displayed = True

                if not text_displayed:
                    safe_print("处理完成，但没有可显示的文本内容")
            else:
                safe_print("无响应内容")

    except Exception as e:
        safe_print(f"Error in streaming response: {e}")
        # Fallback to regular response using AgentScope
        try:
            res = await agent(msg)
            if res.content and len(res.content) > 0:
                # 只显示文本内容，忽略thinking块
                text_displayed = False
                for content in res.content:
                    if isinstance(content, dict):
                        # 跳过thinking块
                        if content.get('type') == 'thinking':
                            continue
                        elif 'text' in content:
                            safe_print(content['text'])
                            text_displayed = True
                        elif 'content' in content:
                            safe_print(content['content'])
                            text_displayed = True
                        elif content.get('type') == 'text':
                            safe_print(content.get('text', str(content)))
                            text_displayed = True
                        else:
                            # 如果是其他类型但不是thinking，也显示
                            if content.get('type') != 'thinking':
                                safe_print(str(content))
                                text_displayed = True
                    else:
                        # 非字典类型，直接显示
                        safe_print(str(content))
                        text_displayed = True

                if not text_displayed:
                    safe_print("处理完成，但没有可显示的文本内容")
            else:
                safe_print("无响应内容")
        except Exception as fallback_error:
            safe_print(f"回退响应错误: {fallback_error}")

async def handle_ocr_command():
    """Handle OCR-specific commands"""
    import os

    # Check if we have an image path or should use clipboard
    if len(sys.argv) == 2:
        # xs ocr - use clipboard
        clipboard_content = get_clipboard_content()
        if not clipboard_content:
            safe_print("剪贴板为空或无法读取内容")
            safe_print("提示：请确保已复制图片到剪贴板，或使用 'xs ocr <图片路径>'")
            return

        image_path = clipboard_content
        prompt = "请识别图片中的所有文字内容。"
    elif len(sys.argv) >= 3:
        # xs ocr <image_path> [prompt]
        image_path = sys.argv[2]

        # Check if image path exists
        if not os.path.exists(image_path):
            safe_print(f"错误: 图片文件不存在: {image_path}")
            return

        # Get prompt if provided
        if len(sys.argv) > 3:
            prompt = " ".join(sys.argv[3:])
        else:
            prompt = "请识别图片中的所有文字内容。"
    else:
        safe_print("OCR命令格式: xs ocr [图片路径] [可选: 识别要求]")
        safe_print("示例1: xs ocr (使用剪贴板图片)")
        safe_print("示例2: xs ocr image.png")
        safe_print("示例3: xs ocr image.png 提取表格内容")
        return

    # Import OCR utilities
    try:
        from utils.ocr_utils import ocr_image
    except ImportError:
        safe_print("错误: OCR功能未正确配置")
        return

    # Perform OCR
    try:
        result = await ocr_image(prompt, image_path)
        if result.content and len(result.content) > 0:
            for content in result.content:
                if isinstance(content, dict) and 'text' in content:
                    safe_print(content['text'])
                elif hasattr(content, 'text'):
                    safe_print(content.text)
                else:
                    safe_print(str(content))
        else:
            safe_print("OCR完成，但未提取到文字内容")
    except Exception as e:
        safe_print(f"OCR处理错误: {e}")

async def main():
    if len(sys.argv) < 2:
        safe_print("只需要在xs命令后输入您的要求即可。")
        safe_print("例如：xs <你要输入的内容>")
        safe_print("示例1：xs 下载视频，http……")
        safe_print("示例2：xs 图片1.png的内容是什么？")
        safe_print("示例3：xs 给1.png中的人物戴上一顶草帽。")
        safe_print("特殊功能：xs p  # 使用剪贴板完整内容作为输入")
        safe_print("高级功能：xs p <问题>  # 对剪贴板完整内容提问")
        safe_print("OCR功能：xs ocr [图片路径] [可选: 识别要求]  # 纯文字识别")
        safe_print("提示：如果剪贴板图片识别失败，请直接使用图片文件路径")
        return  # 无参数时提示用法，直接退出

    # Handle OCR command
    if sys.argv[1] == 'ocr':
        # Ensure Ollama is running before proceeding
        if not ensure_ollama_running():
            safe_print("无法启动Ollama服务，程序退出。")
            return
        await handle_ocr_command()
        return

    # Ensure Ollama is running before proceeding
    if not ensure_ollama_running():
        safe_print("无法启动Ollama服务，程序退出。")
        return

    # Check if the first argument is 'p' for clipboard functionality
    if sys.argv[1] == 'p':
        # Get clipboard content
        clipboard_content = get_clipboard_content()
        if not clipboard_content:
            safe_print("剪贴板为空或无法读取内容")
            safe_print("提示：请确保已复制图片到剪贴板，或直接使用图片文件路径")
            return

        # Use clipboard content as base input
        input_content = clipboard_content

        # Add additional arguments if provided
        if len(sys.argv) > 2:
            additional_text = " ".join(sys.argv[2:])
            input_content = f"{clipboard_content} {additional_text}"

        # 获取当前终端打开的目录路径
        current_dir = os.getcwd()
        # 兼容 Windows 路径
        current_dir = os.path.abspath(current_dir)

        msg = Msg(
            name="user",
            role="user",
            content=input_content + f"当前目录为：{current_dir}"
        )
    else:
        # Normal case:拼接所有参数
        input_content = " ".join(sys.argv[1:])

        # 获取当前终端打开的目录路径
        current_dir = os.getcwd()
        # 兼容 Windows 路径
        current_dir = os.path.abspath(current_dir)

        msg = Msg(
            name="user",
            role="user",
            content=input_content + f"当前目录为：{current_dir}"
        )

    # Use streaming response
    await stream_response(msg)

if __name__ == "__main__":
    asyncio.run(main())