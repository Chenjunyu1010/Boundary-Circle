# 1. 选一个 Python 基础镜像
FROM python:3.9-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖清单到容器里
COPY requirements.txt .

# 4. 安装依赖 (使用清华源加速，或者直接装)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 把当前所有代码复制进容器
COPY . .

# 6. 告诉容器我们要用 8000 端口
EXPOSE 8000

# 7. 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]