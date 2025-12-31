@echo off
REM 小帅终端助手模型配置管理工具
REM 用于快速修改模型配置

set "configFile=D:\code\py\xxzhou\model_config.ini"

echo ========================================
echo 小帅终端助手模型配置管理
echo ========================================
echo.
echo 当前配置文件: %configFile%
echo.

if not exist "%configFile%" (
    echo 错误: 配置文件不存在!
    echo.
    pause
    exit /b 1
)

echo [1] 查看当前配置
echo [2] 修改工具调用模型 (zdolny/qwen3-coder58k-tools:latest)
echo [3] 修改文本模型 (gpt-oss:20b)
echo [4] 修改视觉模型 (gemma3:27b)
echo [5] 使用记事本编辑配置文件
echo [6] 恢复默认配置
echo [0] 退出
echo.
set /p choice=请选择操作:

if "%choice%"=="1" (
    echo.
    echo 当前模型配置:
    type "%configFile%" | findstr /C:"model"
    echo.
    pause
) else if "%choice%"=="2" (
    echo.
    set /p newToolModel=请输入新的工具调用模型名称:
    powershell -Command "(Get-Content '%configFile%') -replace 'tool_model = .*', 'tool_model = %newToolModel%' | Set-Content '%configFile%'"
    echo 工具调用模型已更新为: %newToolModel%
    pause
) else if "%choice%"=="3" (
    echo.
    set /p newTextModel=请输入新的文本模型名称:
    powershell -Command "(Get-Content '%configFile%') -replace 'text_model = .*', 'text_model = %newTextModel%' | Set-Content '%configFile%'"
    echo 文本模型已更新为: %newTextModel%
    pause
) else if "%choice%"=="4" (
    echo.
    set /p newVisionModel=请输入新的视觉模型名称:
    powershell -Command "(Get-Content '%configFile%') -replace 'vision_model = .*', 'vision_model = %newVisionModel%' | Set-Content '%configFile%'"
    echo 视觉模型已更新为: %newVisionModel%
    pause
) else if "%choice%"=="5" (
    echo.
    echo 使用记事本打开配置文件...
    notepad "%configFile%"
) else if "%choice%"=="6" (
    echo.
    echo 恢复默认配置...
    (
        echo # 小帅终端助手模型配置文件
        echo.
        echo [models]
        echo # 工具调用模型（用于代码、下载视频、生成图片等）
        echo tool_model = zdolny/qwen3-coder58k-tools:latest
        echo.
        echo # 常规文本模型（用于日常对话、问答等）
        echo text_model = gpt-oss:20b
        echo.
        echo # 视觉识别模型（用于图片内容识别）
        echo vision_model = gemma3:27b
    ) > "%configFile%"
    echo 默认配置已恢复!
    pause
) else if "%choice%"=="0" (
    exit /b 0
) else (
    echo 无效选择，请重试。
    pause
)

goto :eof