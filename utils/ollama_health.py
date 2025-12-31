import requests
import time
import subprocess
import sys

def check_ollama_health():
    """检查Ollama服务健康状态"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Ollama服务正常"
        else:
            return False, f"Ollama服务响应异常: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到Ollama服务"
    except requests.exceptions.Timeout:
        return False, "Ollama服务响应超时"
    except Exception as e:
        return False, f"检查Ollama服务时出错: {str(e)}"

def restart_ollama_service():
    """重启Ollama服务"""
    try:
        print("正在重启Ollama服务...")

        # 停止Ollama进程
        subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"],
                      capture_output=True, text=True)
        subprocess.run(["taskkill", "/F", "/IM", "ollama app.exe"],
                      capture_output=True, text=True)

        # 等待进程完全停止
        time.sleep(2)

        # 重新启动Ollama
        subprocess.Popen(["ollama", "serve"],
                        creationflags=subprocess.CREATE_NEW_CONSOLE)

        # 等待服务启动
        time.sleep(5)

        return True, "Ollama服务重启完成"
    except Exception as e:
        return False, f"重启Ollama服务失败: {str(e)}"

def main():
    """主函数"""
    print("=== Ollama服务健康检查 ===")

    # 检查服务状态
    is_healthy, message = check_ollama_health()
    print(f"服务状态: {message}")

    if not is_healthy:
        print("\n尝试重启Ollama服务...")
        success, restart_message = restart_ollama_service()
        print(f"重启结果: {restart_message}")

        if success:
            # 再次检查
            time.sleep(3)
            is_healthy, message = check_ollama_health()
            print(f"重启后状态: {message}")

        if not is_healthy:
            print("\n建议手动操作:")
            print("1. 打开任务管理器，结束所有ollama进程")
            print("2. 重新启动Ollama应用程序")
            print("3. 或在命令行运行: ollama serve")
            return False

    print("\n✅ Ollama服务运行正常")
    return True

if __name__ == "__main__":
    main()