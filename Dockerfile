# 使用官方 Python 3.11 slim 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 如果用到数据库驱动（如 asyncmy、cryptography），建议装 gcc build-essential
RUN apt-get update \
 && apt-get install -y gcc build-essential \
 && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装依赖，推荐锁 pip 版本
RUN pip install --upgrade pip==23.3.1
RUN pip install -r requirements.txt

# 复制全部项目代码
COPY . .

# EXPOSE 默认后端端口（如主服务用8000）
EXPOSE 8000

# 用 Uvicorn 启动 FastAPI 项目
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]