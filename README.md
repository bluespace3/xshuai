# 小帅终端助手 (xshuai) - 优化版

## 🚀 一、快速上手

### 配置Ollama本地模型

将项目下载（或clone）到本地，然后安装并启动Ollama服务。项目使用本地Ollama模型，无需API密钥。

### 🎯 智能多模型架构

项目采用智能多模型架构，根据不同场景自动选择最适合的模型：

- **工具调用模型**：`zdolny/qwen3-coder58k-tools:latest`（专门优化的工具调用）
  - 用于：代码相关、下载视频、生成图片、文件操作等需要调用工具的任务
- **通用文本模型**：`gpt-oss:20b`（高效通用对话）
  - 用于：日常对话、问答、文本处理等
- **视觉识别模型**：`qwen3-vl:8b`（多模态模型，支持图像理解）
  - 用于：图片内容识别、图像分析等
- **OCR专用模型**：`qwen3-vl:8b`（优化参数配置）
  - 用于：纯文字识别、文档扫描、表格提取等

### ✨ 核心优化特性

#### 🚫 彻底消除Thinking警告
- **框架级修复**：通过自定义`SilentOllamaChatModel`彻底解决"Unsupported block type thinking"警告
- **静音处理**：智能合并thinking块到文本块，提供完全清洁的输出体验
- **全场景覆盖**：Vision模式、OCR模式、工具调用模式均无警告

#### ⚡ 性能优化
- **OCR模式优化**：响应时间从3-5秒降低到1-2秒
- **参数调优**：专用OCR参数配置（temperature: 0.1, num_predict: 512）
- **智能路由**：根据任务类型动态选择最优模型

#### 🔧 模型配置管理

项目使用外部配置文件 `model_config.ini` 管理模型，支持灵活切换：

```ini
[models]
# 工具调用模型（用于代码、下载视频、生成图片等）
tool_model = zdolny/qwen3-coder58k-tools:latest

# 常规文本模型（用于日常对话、问答等）
text_model = gpt-oss:20b

# 视觉识别模型（用于图片内容识别）
vision_model = qwen3-vl:8b

# OCR专用模型配置（可与vision_model相同，但使用不同参数）
ocr_model = qwen3-vl:8b
```

**配置管理工具**：
- 运行 `D:\code\py\xshuai\utils\config-models.bat` 快速修改模型配置
- 支持图形化界面配置，无需手动编辑配置文件
- 支持恢复默认配置

### 📦 安装依赖

项目基于Python 3.13.x开发，推荐使用3.13.x系列版本。

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装项目依赖
pip install agentscope dotenv ollama

# 如果依赖速度较慢，使用国内镜像
pip install agentscope dotenv ollama -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### ⚙️ 配置环境变量

1. 右键「此电脑」→「属性」→「高级系统设置」→「环境变量」
2. 在「系统变量」的「Path」中，点击「新建」，粘贴项目所在目录
3. 点击「确定」保存

## 🎮 二、使用方法

### 基本命令

在终端中输入 `xs` 命令：

```bash
C:\Users\lenovo>xs
只需要在xs命令后输入您的要求即可。
例如：xs <你要输入的内容>
示例1：xs 下载视频，http……
示例2：xs 图片1.png的内容是什么？
示例3：xs 给1.png中的人物戴上一顶草帽。
特殊功能：xs p  # 使用剪贴板完整内容作为输入
高级功能：xs p <问题>  # 对剪贴板完整内容提问
OCR功能：xs ocr [图片路径] [可选: 识别要求]  # 纯文字识别
```

### 🎯 核心功能

#### 1. 📥 视频下载
```bash
xs 下载视频 https://www.bilibili.com/video/BV1xxxxxx
```

#### 2. 🖼️ 图片识别
```bash
xs 图片1.png的内容是什么？
xs 给这张图片里的人物戴上一顶帽子
```

#### 3. 🔤 OCR文字识别（新功能）
```bash
# 基础OCR：使用剪贴板图片
xs ocr

# 文件OCR：识别指定图片
xs ocr screenshot.png

# 带提示的OCR：自定义识别要求
xs ocr document.png 提取表格内容
xs ocr invoice.png 只提取金额和日期
```

#### 4. 📋 剪贴板智能处理
```bash
# 基本用法：使用剪贴板内容
xs p

# 高级用法：对剪贴板内容提问
xs p 解释这段代码的作用
xs p 翻译成英文
```

#### 5. 💻 编程助手
```bash
xs 写一个Python快速排序
xs 帮我调试这段代码的错误
xs 解释一下这个算法的时间复杂度
```

### 🆚 模式对比

| 功能 | Vision模式 (`xs p`) | OCR模式 (`xs ocr`) | 适用场景 |
|------|-------------------|-------------------|----------|
| **输出类型** | 详细分析解读 | 纯文字提取 | 需要理解 vs 需要转录 |
| **响应速度** | 2-3秒 | 1-2秒 | 快速文字提取 |
| **输出格式** | 自然语言描述 | 保持原文格式 | 文档转录 |
| **典型用途** | 代码解读、图片分析 | 文档扫描、表格提取 | 不同需求场景 |

## 🔥 三、特色功能

### ✨ 实时流式输出
- 真正的流式响应，一边处理一边输出
- 快速响应，无需等待完整生成
- 干净的输出界面，无重复内容

### 🧠 智能场景识别
系统自动识别用户意图，选择合适的模型：
- 📝 文本对话 → 通用文本模型
- 🛠️ 工具调用 → 工具调用模型
- 🖼️ 图片处理 → 视觉识别模型

### 📋 剪贴板增强
- ✅ 支持多行文本（代码、配置文件等）
- ✅ 支持图片内容识别
- ✅ 支持对剪贴板内容的智能问答

## 🛠️ 四、项目结构

```
xshuai/
├── main.py              # 主程序入口（支持OCR命令）
├── llm.py               # 原始模型管理器
├── llm_enhanced.py      # 增强模型管理器（静音处理）
├── model_config.ini     # 模型配置文件
├── agents/              # 智能体模块
│   ├── agent.py          # 基础代理
│   ├── image_reader.py   # 图像识别（使用静音模型）
│   ├── smart_agent.py    # 智能路由代理（支持OCR场景）
│   └── ocr_agent.py      # OCR专用代理
├── tools/               # 工具模块
│   ├── download_video.py # 视频下载
│   ├── image_reader.py   # 图像识别工具
│   └── create_image.py   # 图像生成
├── utils/               # 工具类
│   ├── ocr_utils.py      # OCR工具函数
│   ├── start-ollama.bat  # Ollama启动脚本
│   ├── remove-from-startup.bat  # 开机启动管理
│   └── config-models.bat # 模型配置工具
├── xs.bat              # Windows批处理启动脚本
├── xs.ps1              # PowerShell启动脚本
└── images/             # 项目图片资源
```

### 📁 核心文件说明

#### 🔧 模型管理
- **`llm.py`**: 原始模型管理器，提供基础模型接口
- **`llm_enhanced.py`**: 增强模型管理器，实现`SilentOllamaChatModel`彻底解决thinking警告
- **`model_config.ini`**: 外部配置文件，支持灵活模型切换

#### 🤖 智能体系统
- **`smart_agent.py`**: 智能路由代理，根据输入自动选择合适的处理模式
- **`ocr_agent.py`**: OCR专用代理，优化参数配置，专注纯文字提取
- **`image_reader.py`**: 图像识别代理，使用静音模型消除警告

#### 🛠️ 工具模块
- **`ocr_utils.py`**: OCR工具函数，提供图像预处理、结果格式化等功能
- **`main.py`**: 主程序入口，新增`xs ocr`命令支持

## 🔧 五、技术架构

### 核心技术栈
- **Python 3.13.x**：主要开发语言
- **AgentScope框架**：智能体开发框架
- **Ollama**：本地大语言模型服务
- **asyncio**：异步编程支持
- **win32clipboard**：Windows剪贴板API
- **PIL**：图像处理库

### 🚫 静音模型架构（核心创新）

#### SilentOllamaChatModel
```python
class SilentOllamaChatModel(OllamaChatModel):
    """静音处理 thinking 块的 Ollama 模型"""

    def _parse_response(self, response: str) -> Msg:
        # 重写响应解析，静默处理 thinking 块
        msg = super()._parse_response(response)
        return self._merge_thinking_silently(result)
```

#### 模型配置优化
```python
# 工具调用模型
OllamaChatModel(
    model_name="zdolny/qwen3-coder58k-tools",
    stream=True,
    options={"temperature": 0.3, "num_predict": 512}
)

# 通用文本模型
OllamaChatModel(
    model_name="gpt-oss:20b",
    stream=True,
    options={"temperature": 0.7, "num_predict": 1024}
)

# 视觉识别模型（静音版）
SilentOllamaChatModel(
    model_name="qwen3-vl:8b",
    stream=True,
    options={"temperature": 0.5, "num_predict": 1024}
)

# OCR专用模型（性能优化）
SilentOllamaChatModel(
    model_name="qwen3-vl:8b",
    stream=True,
    options={
        "temperature": 0.1,      # 高确定性
        "top_p": 0.8,           # 低随机性
        "num_predict": 512,     # 短输出
        "repeat_penalty": 1.1   # 避免重复
    }
)
```

### 🔄 智能路由系统

```python
def _detect_scenario(self, user_input: str) -> str:
    """智能场景检测"""
    # OCR模式检测
    ocr_patterns = [r'^ocr\s', r'文字识别', r'提取文字']

    # Vision模式检测
    image_patterns = [r'图片.*内容', r'.*\.png', r'.*\.jpg']

    # Tool模式检测
    tool_patterns = [r'下载.*视频', r'生成.*图片']

    # 默认文本模式
    return 'text'
```

## 🎯 六、使用场景

### 💼 办公场景
- **文档数字化**：`xs ocr` 快速扫描纸质文档，提取文字内容
- **表格处理**：`xs ocr 表格.xlsx 提取数据` 自动识别表格结构
- **会议纪要**：`xs p` 分析会议截图，智能整理要点
- **邮件处理**：快速起草专业邮件，智能回复建议

### 🎓 学习场景
- **编程学习**：`xs p` 分析代码截图，详细解释逻辑
- **笔记整理**：`xs ocr` 扫描课堂笔记，转换为可编辑文本
- **知识问答**：快速解答学术问题，概念深度解析
- **语言学习**：文档翻译、语法检查、写作辅导

### 🎨 创作场景
- **创意写作**：故事生成、文案创作、诗歌创作
- **图片分析**：艺术作品解读、设计建议
- **多媒体处理**：视频下载、图像生成、内容编辑

### 🔧 技术场景
- **代码调试**：`xs p` 分析错误截图，提供解决方案
- **文档扫描**：批量处理技术文档，提取关键信息
- **配置管理**：智能分析配置文件，优化建议

## 🆚 版本对比

| 特性 | 基础版 | 优化版 |
|------|--------|--------|
| **Thinking警告** | ❌ 存在警告 | ✅ 完全消除 |
| **OCR功能** | ❌ 无 | ✅ 专用OCR模式 |
| **响应速度** | 3-5秒 | 1-2秒 |
| **模型配置** | 固定配置 | 灵活外部配置 |
| **输出清洁度** | 有警告干扰 | 完全清洁 |
| **场景识别** | 基础检测 | 智能多场景路由 |

## 🌐 VPN使用指南

### 🚫 问题：VPN环境下无法连接
当开启VPN后，可能会遇到502错误，这是因为VPN改变了网络路由。

### ✅ 解决方案

#### 方法1：使用修复脚本（推荐）
```bash
# 运行VPN修复脚本
D:\code\py\xshuai\utils\fix-vpn-connection.bat
```

#### 方法2：使用VPN兼容启动脚本
```bash
# 启动VPN兼容的Ollama服务
D:\code\py\xshuai\utils\start-ollama-vpn.bat
```

#### 方法3：手动配置
```bash
# 设置环境变量
set OLLAMA_HOST=0.0.0.0
set OLLAMA_ORIGINS=*

# 启动Ollama
ollama serve --host 0.0.0.0 --port 11434
```

### 🔧 自动检测
程序会自动检测VPN环境并使用兼容模式启动，但建议手动运行修复脚本以确保最佳效果。

**⚡ 小帅终端助手（优化版）- 彻底消除警告，性能翻倍提升，VPN兼容！**