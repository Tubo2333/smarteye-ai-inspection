"""
SmartEye 桌面版入口 — 独立窗口，无需浏览器

用法: python desktop_app.py

首次运行前需安装 pywebview:
    pip install pywebview
"""
import sys
import time
import threading
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# ── 启动后端 (FastAPI) ──
def start_backend():
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )

# ── 启动前端 (Streamlit) ──
def start_frontend():
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501", "--server.headless", "true",
         "--server.address", "127.0.0.1",
         "--browser.gatherUsageStats", "false",
         "--logger.level", "error"],
        cwd=str(PROJECT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    print("Starting SmartEye Desktop...")

    # 1. 启动后端线程
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()

    # 2. 等后端就绪
    print("Waiting for backend...")
    import urllib.request
    for i in range(30):
        time.sleep(0.5)
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
            print("Backend ready.")
            break
        except Exception:
            pass

    # 3. 启动前端进程（Streamlit 用 subprocess 更稳定）
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

    # 4. 等前端就绪
    print("Waiting for frontend...")
    time.sleep(4)

    # 5. 创建桌面窗口
    print("Opening desktop window...")
    import webview
    webview.create_window(
        title="SmartEye — AI 视觉质检系统",
        url="http://localhost:8501",
        width=1400,
        height=900,
        min_size=(1024, 700),
        resizable=True,
    )
    webview.start()

    # 6. 窗口关闭 → 清理
    print("Shutting down...")
    frontend_proc.terminate()
    frontend_proc.wait()
    print("SmartEye Desktop closed.")


if __name__ == "__main__":
    main()
