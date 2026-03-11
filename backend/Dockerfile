FROM python:3.13

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    pkg-config \
    libmariadb-dev-compat \
    libssl-dev \
    libffi-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    tzdata \
    netcat-openbsd \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝 Django 项目
COPY . /app/

# 拷贝 entrypoint
COPY entrypoint.sh /entrypoint.sh

# 修复换行、赋权、创建用户并调整目录权限
RUN sed -i 's/\r$//' /entrypoint.sh \
    && chmod +x /entrypoint.sh \
    && useradd -m appuser \
    && chown -R appuser:appuser /app \
    && chown appuser:appuser /entrypoint.sh

USER appuser


# 对外暴露后端端口
EXPOSE 8000

# 使用 entrypoint.sh 启动流程（等待DB → migrate → loaddata → gunicorn）
ENTRYPOINT ["/entrypoint.sh"]

