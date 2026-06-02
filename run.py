#!/usr/bin/env python
"""
SmartEye 一键启动脚本

用法（任选一种）：
  1. 双击 run.py（如果 .py 关联了 Python）
  2. 终端输入：python run.py
  3. 终端输入：python3 run.py

首次运行会自动完成：
  - 创建虚拟环境
  - 安装所有依赖（使用国内镜像加速）
  - 下载 ChromaDB 模型
  - 构建 RAG 知识库
  - 启动后端 + 前端
  - 打开浏览器

之后再运行直接启动，跳过安装步骤。
"""
import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
VENV_DIR = PROJECT_DIR / "venv"
CHROMADB_DIR = PROJECT_DIR / "data" / "chromadb"

# 国内镜像（加速下载）
MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"
HF_MIRROR = "https://hf-mirror.com"


def run(cmd, **kwargs):
    """运行命令，实时输出"""
    env = os.environ.copy()
    env["HF_ENDPOINT"] = HF_MIRROR
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.run(cmd, cwd=PROJECT_DIR, env=env, **kwargs)


def pip_path():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    return str(VENV_DIR / "bin" / "pip")


def python_path():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def main():
    print("""
╔══════════════════════════════════════════════════╗
║          SmartEye — AI 视觉质检系统               ║
║              一键启动脚本 v1.0                    ║
╚══════════════════════════════════════════════════╝
    """)

    # ═════════════════════════════════════════════════════
    # Step 1: 创建虚拟环境
    # ═════════════════════════════════════════════════════
    if not VENV_DIR.exists():
        step("Step 1/6: 创建虚拟环境")
        run([sys.executable, "-m", "venv", "venv"])
        print("[OK] 虚拟环境已创建")
    else:
        print("[SKIP] 虚拟环境已存在")

    # ═════════════════════════════════════════════════════
    # Step 2: 安装 PyTorch
    # ═════════════════════════════════════════════════════
    step("Step 2/6: 安装 PyTorch (CUDA)")
    result = run([pip_path(), "install", "torch", "torchvision",
                  "--index-url", "https://download.pytorch.org/whl/cu121"],
                 capture_output=True, text=True)
    # 忽略已安装的提示
    if result.returncode != 0:
        # 尝试 CPU 版本
        print("[WARN] CUDA 版本安装失败，改用 CPU 版本...")
        run([pip_path(), "install", "torch", "torchvision",
             "-i", MIRROR])
    print("[OK] PyTorch 就绪")

    # ═════════════════════════════════════════════════════
    # Step 3: 安装依赖
    # ═════════════════════════════════════════════════════
    step("Step 3/6: 安装 Python 依赖 (首次约 5-15 分钟)")
    deps = [
        "langchain", "langgraph", "langchain-anthropic", "langchain-core",
        "langchain-text-splitters", "fastapi", "uvicorn", "streamlit",
        "python-dotenv", "python-multipart", "opencv-python", "ultralytics",
        "chromadb", "python-docx", "pytest", "pytest-asyncio", "httpx",
        "pandas", "matplotlib", "plotly", "pyyaml", "jinja2", "pydantic",
        "sentence-transformers", "numpy", "pillow",
    ]
    run([pip_path(), "install", "-i", MIRROR] + deps)
    print("[OK] 依赖安装完成")

    # ═════════════════════════════════════════════════════
    # Step 4: 安装 SAM 2.1
    # ═════════════════════════════════════════════════════
    step("Step 4/6: 安装 SAM 2.1")
    result = run([pip_path(), "install", "sam2", "-i", MIRROR],
                 capture_output=True, text=True)
    if result.returncode != 0:
        print("[WARN] SAM 2.1 安装失败，尝试 SAM 1 fallback...")
        run([pip_path(), "install", "segment-anything", "-i", MIRROR])
    print("[OK] SAM 就绪")

    # ═════════════════════════════════════════════════════
    # Step 5: 构建 RAG 知识库
    # ═════════════════════════════════════════════════════
    step("Step 5/6: 构建知识库 (首次需下载 80MB 模型)")
    result = run([python_path(), "-c", """
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
try:
    from backend.rag.vector_store import build_knowledge_base, get_knowledge_stats
    stats = get_knowledge_stats()
    if stats.get('total_chunks', 0) > 0:
        print(f"[SKIP] 知识库已有 {stats['total_chunks']} 条索引")
    else:
        count = build_knowledge_base()
        print(f"[OK] 知识库构建完成: {count} 条索引")
except Exception as e:
    print(f"[WARN] 知识库构建跳过: {e}")
"""], capture_output=False)
    print("[OK] 知识库就绪")

    # ═════════════════════════════════════════════════════
    # Step 6: 启动服务
    # ═════════════════════════════════════════════════════
    step("Step 6/6: 清理旧进程 + 启动服务")

    # 先杀掉占用端口 8000 和 8501 的旧进程
    import socket
    for port in [8000, 8501]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
            s.close()
            print(f"[INFO] 端口 {port} 被占用，尝试清理...")
            if os.name == "nt":
                os.system(f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :{port}\') do taskkill //F //PID %a 2>nul')
            else:
                os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null")
            time.sleep(2)
        except Exception:
            pass  # 端口空闲，无需清理

    # 启动 FastAPI 后端（后台进程）
    print("[INFO] 启动后端 (FastAPI)...")
    backend_proc = subprocess.Popen(
        [python_path(), "-c",
         "import uvicorn; uvicorn.run('backend.main:app', host='127.0.0.1', port=8000)"],
        cwd=PROJECT_DIR,
        env={**os.environ, "HF_ENDPOINT": HF_MIRROR, "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待后端就绪
    print("[INFO] 等待后端启动...")
    for i in range(30):
        time.sleep(0.5)
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=1)
            print("[OK] 后端已就绪")
            break
        except Exception:
            pass
    else:
        print("[WARN] 后端可能启动较慢，继续启动前端...")

    # 启动 Streamlit 前端（后台进程）
    print("[INFO] 启动前端 (Streamlit)...")
    frontend_proc = subprocess.Popen(
        [python_path(), "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501", "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=PROJECT_DIR,
        env={**os.environ, "HF_ENDPOINT": HF_MIRROR, "PYTHONUNBUFFERED": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 等待前端就绪
    print("[INFO] 等待前端启动...")
    time.sleep(3)

    # 打开浏览器
    print("[INFO] 打开浏览器...")
    webbrowser.open("http://localhost:8501")

    print(f"""
╔══════════════════════════════════════════════════╗
║  SmartEye 已启动！                                ║
║                                                  ║
║  前端界面:  http://localhost:8501                 ║
║  API 文档:  http://localhost:8000/docs            ║
║                                                  ║
║  按 Ctrl+C 停止所有服务                           ║
╚══════════════════════════════════════════════════╝
    """)

    # 保持运行，直到用户按 Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 正在关闭...")
        frontend_proc.terminate()
        backend_proc.terminate()
        frontend_proc.wait()
        backend_proc.wait()
        print("[OK] 已关闭。下次直接运行 python run.py 即可。")


if __name__ == "__main__":
    main()
