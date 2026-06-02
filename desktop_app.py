"""
SmartEye 桌面版入口 — 独立窗口，无需浏览器，自动隐藏命令行

用法: python desktop_app.py

首次使用需安装 pywebview:
    pip install pywebview
"""
import sys
import os
import time
import threading
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# ── 日志文件（所有输出重定向到此）──
LOG_FILE = PROJECT_DIR / "data" / "desktop.log"

# ── 隐藏控制台 ──
def hide_console():
    """隐藏当前进程的控制台窗口"""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd != 0:
            user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass

def show_console():
    """显示控制台窗口"""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if hwnd != 0:
            user32.ShowWindow(hwnd, 5)  # 5 = SW_SHOW
    except Exception:
        pass

# ── 启动后端 ──
def start_backend():
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )


def main():
    # 重定向输出到日志文件
    log_f = open(LOG_FILE, "w", encoding="utf-8")
    sys.stdout = log_f
    sys.stderr = log_f

    print("SmartEye Desktop starting...")
    print(f"PID: {os.getpid()}")

    # 启动后端线程
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 等后端就绪
    import urllib.request
    for i in range(30):
        time.sleep(0.5)
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
            print("Backend ready.")
            break
        except Exception:
            pass

    # 启动前端进程
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501", "--server.headless", "true",
         "--server.address", "127.0.0.1",
         "--browser.gatherUsageStats", "false",
         "--logger.level", "error"],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(4)

    # ── 隐藏控制台 ──
    hide_console()

    # ── 创建桌面窗口 ──
    import webview

    # 暴露 toggle_console 给前端 JS
    class Api:
        def toggle_console(self):
            """前端可调用 window.pywebview.api.toggle_console()"""
            show_console()
            return "Console shown"

    api = Api()

    window = webview.create_window(
        title="SmartEye — AI 视觉质检系统",
        url="http://localhost:8501",
        width=1400,
        height=900,
        min_size=(1024, 700),
        resizable=True,
        js_api=api,
    )

    webview.start()

    # ── 窗口关闭 → 清理 ──
    print("Window closed, shutting down...")
    frontend_proc.terminate()
    frontend_proc.wait()
    print("Done.")
    log_f.close()


if __name__ == "__main__":
    main()
