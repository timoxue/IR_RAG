# IR 问答审核系统 - Streamlit 版本

基于 Streamlit 的轻量级问答审核界面，专注于审核工作流程。

## 功能模块

1. **单问即答** - 实时测试双轨 RAG 问答
2. **审核工作台** - 审核 AI 生成的答案
3. **标准回答管理** - 管理标准回答库
4. **Prompt 管理** - 管理提示词模板
5. **系统指标** - 查看系统运行指标

## 本地运行

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## Docker 运行

```bash
docker build -t irrag-streamlit -f streamlit_app/Dockerfile .
docker run -p 8501:8501 -e BACKEND_API_URL=http://host.docker.internal:8000 irrag-streamlit
```

## 环境变量

- `BACKEND_API_URL` - 后端 API 地址（默认：http://localhost:8000）
- `USER_EMAIL` - 当前用户邮箱（默认：ir@example.com）

## 访问地址

http://localhost:8501

