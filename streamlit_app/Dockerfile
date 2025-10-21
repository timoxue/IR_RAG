FROM python:3.11-slim

WORKDIR /app

# 配置清华源加速
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装依赖
COPY streamlit_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY streamlit_app/app.py .

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

