#!/usr/bin/env python
"""
SmartEye 便携版构建脚本

将整个项目 + Python 运行环境 + 所有依赖 + 模型打包为独立文件夹。
打包后的文件夹可复制到任意 Windows 电脑，无需安装 Python，双击即用。

用法:
    python scripts/build_portable.py

输出:
    dist/SmartEye/   — 便携版文件夹（可压缩为 .zip 分发）
"""
import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DIST_DIR = PROJECT_DIR / "dist" / "SmartEye"
PYTHON_VERSION = "3.12.10"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# 需要复制的项目文件/目录
INCLUDE = [
    "backend", "frontend", "data", "scripts",
    "requirements.txt", "run.py", "启动SmartEye.bat",
    ".env.example",
]

# 不打包的内容
EXCLUDE_PATTERNS = [
    "__pycache__", "*.pyc", ".git", "venv", "dist",
    "data/pcb_dataset", "data/chromadb", "backend/models/runs",
    "huggingface-space", "docs", "tests", "notebooks",
]


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def should_include(path: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.replace("/", os.sep) in path.replace("/", os.sep):
            return False
    return True


def main():
    # ═══════════════════════════════════════════════════
    # Step 1: 准备输出目录
    # ═══════════════════════════════════════════════════
    step("Step 1/6: 准备输出目录")
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] {DIST_DIR}")

    # ═══════════════════════════════════════════════════
    # Step 2: 下载嵌入式 Python
    # ═══════════════════════════════════════════════════
    step("Step 2/6: 下载嵌入式 Python 3.12")
    embed_zip = DIST_DIR / "python-embed.zip"
    if not embed_zip.exists():
        print(f"下载 {PYTHON_EMBED_URL} ...")
        urllib.request.urlretrieve(PYTHON_EMBED_URL, embed_zip)
        print(f"[OK] 已下载 {embed_zip.stat().st_size / 1024 / 1024:.0f} MB")
    else:
        print("[SKIP] 已存在")

    # 解压
    python_dir = DIST_DIR / "python"
    with zipfile.ZipFile(embed_zip, 'r') as zf:
        zf.extractall(python_dir)
    print(f"[OK] Python 解压到 {python_dir}")

    # 启用 pip（嵌入式 Python 默认禁用）
    python_exe = python_dir / "python.exe"
    pth_file = list(python_dir.glob("python*._pth"))[0]
    # 取消 import site 的注释以启用 pip
    content = pth_file.read_text()
    if "#import site" in content:
        content = content.replace("#import site", "import site")
        pth_file.write_text(content)
    print("[OK] pip 已启用")

    # ═══════════════════════════════════════════════════
    # Step 3: 安装 pip + 依赖到嵌入式 Python
    # ═══════════════════════════════════════════════════
    step("Step 3/6: 安装 pip 和 Python 依赖（需要网络，约 10-20 分钟）")

    # 下载 get-pip.py
    get_pip = DIST_DIR / "get-pip.py"
    if not get_pip.exists():
        urllib.request.urlretrieve(PIP_URL, get_pip)

    # 安装 pip
    subprocess.run([str(python_exe), str(get_pip), "--no-warn-script-location"],
                   cwd=str(DIST_DIR), check=True)

    pip_exe = python_dir / "Scripts" / "pip.exe"

    # 安装 PyTorch (CUDA)
    print("[INFO] 安装 PyTorch CUDA ...")
    subprocess.run([
        str(pip_exe), "install", "torch", "torchvision",
        "--index-url", "https://download.pytorch.org/whl/cu121",
    ], cwd=str(DIST_DIR), check=True)

    # 安装项目依赖
    print("[INFO] 安装项目依赖 ...")
    subprocess.run([
        str(pip_exe), "install",
        "langchain", "langgraph", "langchain-anthropic", "langchain-core",
        "langchain-text-splitters", "fastapi", "uvicorn", "streamlit",
        "python-dotenv", "python-multipart", "opencv-python", "ultralytics",
        "chromadb", "python-docx", "pandas", "matplotlib", "plotly",
        "pyyaml", "jinja2", "pydantic", "sentence-transformers",
        "numpy", "pillow", "httpx",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
    ], cwd=str(DIST_DIR), check=True)

    print("[OK] 依赖安装完成")

    # ═══════════════════════════════════════════════════
    # Step 4: 复制项目文件
    # ═══════════════════════════════════════════════════
    step("Step 4/6: 复制项目文件")

    for item in INCLUDE:
        src = PROJECT_DIR / item
        dst = DIST_DIR / item
        if not src.exists():
            print(f"[SKIP] {item} (不存在)")
            continue

        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS),
                            dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        print(f"[OK] {item}")

    # 确保 sample_images 带过去
    sample_src = PROJECT_DIR / "data" / "sample_images"
    sample_dst = DIST_DIR / "data" / "sample_images"
    if sample_src.exists():
        if sample_dst.exists():
            shutil.rmtree(sample_dst)
        shutil.copytree(sample_src, sample_dst)
        print(f"[OK] data/sample_images ({len(list(sample_dst.glob('*')))} files)")

    # YOLO 模型
    model_src = PROJECT_DIR / "backend" / "models" / "yolov8_pcb.pt"
    model_dst = DIST_DIR / "backend" / "models" / "yolov8_pcb.pt"
    if model_src.exists():
        model_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(model_src, model_dst)
        print(f"[OK] YOLO model ({model_src.stat().st_size / 1024 / 1024:.0f} MB)")
    else:
        print("[WARN] YOLO model not found, will use pre-trained on first run")

    # ═══════════════════════════════════════════════════
    # Step 5: 创建启动器
    # ═══════════════════════════════════════════════════
    step("Step 5/6: 创建启动脚本")

    launcher = DIST_DIR / "启动SmartEye.bat"
    launcher.write_text(f"""@echo off
cd /d "%~dp0"
title SmartEye

echo ================================================
echo   SmartEye - AI Visual Inspection System
echo   Portable Edition
echo ================================================
echo.

REM 首次运行构建知识库
if not exist "data\\chromadb" (
    echo [INFO] First run: building knowledge base...
    python\\python.exe -c "import os; os.environ['HF_ENDPOINT']='https://hf-mirror.com'; from backend.rag.vector_store import build_knowledge_base; build_knowledge_base()" 2>nul
)

REM 启动
start "" python\\python.exe run.py

echo.
echo SmartEye is starting...
echo Frontend: http://localhost:8501
echo Backend:  http://localhost:8000/docs
echo.
echo Close this window after you finish using SmartEye.
pause
""", encoding="utf-8")
    print("[OK] 启动器已创建")

    # ═══════════════════════════════════════════════════
    # Step 6: 汇总
    # ═══════════════════════════════════════════════════
    step("Step 6/6: 打包完成")

    total_size = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file())
    print(f"""
╔══════════════════════════════════════════════════╗
║  SmartEye 便携版已构建完成                        ║
║                                                  ║
║  位置: {str(DIST_DIR)}
║  大小: {total_size / 1024 / 1024 / 1024:.1f} GB
║                                                  ║
║  分发方式:                                        ║
║  1. 压缩 dist/SmartEye/ 为 .zip                   ║
║  2. 发给对方，解压即可                            ║
║  3. 双击 启动SmartEye.bat 运行                    ║
║                                                  ║
║  对方无需安装 Python、CUDA 或任何依赖             ║
╚══════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
