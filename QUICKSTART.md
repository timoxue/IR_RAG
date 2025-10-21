# 🚀 快速入门指南

## 5 分钟快速启动

### Step 1: 启动服务 (2 分钟)

```bash
# 克隆项目
git clone <repository-url>
cd IR_RAG

# 启动所有服务
docker compose up -d

# 等待服务启动完成
docker compose ps
```

预期输出：
```
NAME              STATUS
irrag-mysql       Up (healthy)
irrag-backend     Up
irrag-frontend    Up
irrag-streamlit   Up
irrag-adminer     Up
```

### Step 2: 配置 API Keys (1 分钟)

编辑 `docker-compose.yml`，填入你的 API Keys：

```yaml
environment:
  - RAGFLOW_API_KEY=ragflow-YOUR_KEY    # 从 RAGFlow 获取
  - QWEN_API_KEY=sk-YOUR_KEY            # 从阿里云获取
```

重启后端：
```bash
docker compose restart backend
```

### Step 3: 访问界面 (1 分钟)

打开浏览器访问：

**🎨 Streamlit 审核系统** (推荐)
- 地址：http://localhost:8501
- 功能：单问即答、审核工作台、标准答案管理

**🖥️ Vue3 管理控制台**
- 地址：http://localhost:5173
- 功能：完整的管理功能

**📚 API 文档**
- 地址：http://localhost:8000/docs

### Step 4: 创建第一个标准答案 (1 分钟)

在 Streamlit 界面：
1. 点击左侧 **"📚 标准回答管理"**
2. 填写表单：
   - Topic Key: `test_answer`
   - 内容: `这是一个测试标准答案`
   - 强约束: 不勾选
3. 点击 **"💾 保存"**

### Step 5: 测试问答 (1 分钟)

1. 点击 **"📝 单问即答"**
2. 填写：
   - 知识库A ID: `9d836ce6ae7c11f08b543a9883fcddc0` (你的 RAGFlow dataset ID)
   - 问题: `测试问题`
3. 点击 **"🚀 提问"**

---

## 常见场景操作

### 场景 1: 批量上传公司文档

**使用纯 ZIP 模式**（最简单）：

1. 准备 ZIP 文件，包含所有 PDF/DOCX：
   ```
   company_docs.zip
   ├── 2024年报.pdf
   ├── Q3财报.pdf
   └── 研发公告.pdf
   ```

2. 在 Vue3 界面上传：
   - 访问 http://localhost:5173
   - 进入"批量导入"标签
   - 选择 ZIP 文件
   - 填写 kb_a_id
   - 上传

3. 查看处理状态：
   - 在 RAGFlow 界面查看文档状态
   - 等待从 Pending → Processing → Completed

### 场景 2: 审核 AI 生成的答案

1. 访问 Streamlit 审核系统: http://localhost:8501
2. 点击 **"✅ 审核工作台"**
3. 从左侧任务列表选择一个任务
4. 查看：
   - 初稿 vs 对齐后
   - 对齐模式和相似度
   - 证据来源
   - 冲突检测
5. 填写审核意见
6. 点击 **通过/退回/拒绝**

### 场景 3: 将优秀答案升级为标准

在审核工作台：
1. 选择一个优秀的答案
2. 滚动到 **"⭐ 升级为标准回答"** 部分
3. 填写 Topic Key (如：`product_intro`)
4. 选择是否强约束
5. 点击 **"⭐ 保存为标准回答"**

---

## 故障排查速查表

### 问题：后端无法连接数据库

```bash
# 检查 MySQL 状态
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 测试连接
docker exec irrag-mysql mysql -uir -pir_password ir_rag -e "SELECT 1;"

# 解决方案：重启 MySQL
docker compose restart mysql
docker compose restart backend
```

### 问题：文件上传失败 413

**原因**：文件太大  
**检查**：`frontend/nginx.conf` 中的 `client_max_body_size`  
**默认**：500M（已配置）

### 问题：RAGFlow 文档一直 Pending

**原因**：未触发解析  
**解决**：
1. 确保后端已更新（包含自动触发解析的代码）
2. 重新上传文件
3. 或在 RAGFlow 界面手动点击 Parse

### 问题：LLM 调用失败

```bash
# 检查配置
docker compose logs backend | grep -i "qwen\|llm\|api"

# 验证 API Key
curl https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer sk-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-max",
    "messages": [{"role": "user", "content": "test"}]
  }'
```

### 问题：Streamlit 无法访问后端

**检查网络**：
```bash
# 从 Streamlit 容器测试后端
docker exec irrag-streamlit curl http://backend:8000/api/v1/health
```

**检查配置**：
```yaml
# docker-compose.yml
environment:
  - BACKEND_API_URL=http://backend:8000  # 容器间通信
```

---

## 开发工作流

### 日常开发

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建（如有更改）
docker compose build backend streamlit

# 3. 启动服务
docker compose up -d

# 4. 查看日志
docker compose logs -f backend streamlit

# 5. 进行开发...

# 6. 停止服务
docker compose down
```

### 数据库变更

```bash
# 1. 修改模型
vim backend/app/models/models.py

# 2. 生成迁移
docker exec irrag-backend alembic revision --autogenerate -m "add new field"

# 3. 应用迁移
docker exec irrag-backend alembic upgrade head

# 4. 验证
docker exec irrag-mysql mysql -uir -pir_password ir_rag -e "DESCRIBE table_name;"
```

### 前端开发

```bash
# 开发模式（热重载）
cd frontend
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

---

## 数据备份与恢复

### 备份

```bash
# 备份数据库
docker exec irrag-mysql mysqldump -uir -pir_password ir_rag > backup_$(date +%Y%m%d).sql

# 备份上传文件
docker cp irrag-backend:/app/storage ./storage_backup_$(date +%Y%m%d)
```

### 恢复

```bash
# 恢复数据库
docker exec -i irrag-mysql mysql -uir -pir_password ir_rag < backup_20251021.sql

# 恢复文件
docker cp ./storage_backup_20251021 irrag-backend:/app/storage
```

---

## 生产部署检查清单

- [ ] 修改所有默认密码
- [ ] 配置正确的 CORS 来源
- [ ] 启用 HTTPS/TLS
- [ ] 配置数据库备份策略
- [ ] 设置日志轮转和清理
- [ ] 配置监控和告警
- [ ] 实施访问控制
- [ ] 配置速率限制
- [ ] 准备应急响应预案
- [ ] 进行负载测试
- [ ] 配置 CDN（如需要）
- [ ] 准备回滚方案

---

## 获取帮助

- 📖 查看 [README.md](README.md) - 完整项目说明
- 🏗️ 查看 [ARCHITECTURE.md](ARCHITECTURE.md) - 架构详解
- 💬 提交 Issue - 报告问题或建议
- 📧 联系团队 - ir@example.com

---

**Happy Coding! 🎉**

