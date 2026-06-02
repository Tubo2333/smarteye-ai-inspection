# SmartEye — 一键部署 Docker 镜像
# 构建: docker build -t smarteye .
# 运行: docker run -p 8501:8501 -p 8000:8000 smarteye

FROM python:3.12-slim

# 系统依赖（OpenCV 需要 libGL）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存层）
COPY requirements.txt .

# 安装 PyTorch CPU 版（Docker 通常无 GPU）
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir sentence-transformers

# 复制项目代码
COPY . .

# 构建知识库（首次启动时也会自动检查）
ENV HF_ENDPOINT=https://hf-mirror.com
RUN python -c "from backend.rag.vector_store import build_knowledge_base; build_knowledge_base()" || true

# 暴露端口
EXPOSE 8000 8501

# 启动脚本
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
