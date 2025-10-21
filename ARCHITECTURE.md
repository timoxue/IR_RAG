# 系统架构说明

## 总体架构

```
┌───────────────────────────────────────────────────────────────────┐
│                          用户层                                    │
│  ┌─────────────┐         ┌─────────────┐         ┌─────────────┐ │
│  │  浏览器     │         │  移动端     │         │  API 客户端  │ │
│  └─────────────┘         └─────────────┘         └─────────────┘ │
└──────────────┬────────────────┬────────────────────┬──────────────┘
               │                │                    │
┌──────────────┴────────────────┴────────────────────┴──────────────┐
│                         前端层                                     │
│  ┌──────────────────────┐         ┌──────────────────────┐       │
│  │   Vue3 + Element     │         │     Streamlit        │       │
│  │   (管理控制台)        │         │    (审核工作台)       │       │
│  │   Port: 5173         │         │    Port: 8501        │       │
│  │                      │         │                      │       │
│  │  • 批量导入          │         │  • 单问即答          │       │
│  │  • 文档管理          │         │  • 审核工作台        │       │
│  │  • 系统配置          │         │  • 标准答案管理      │       │
│  └──────────────────────┘         └──────────────────────┘       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    HTTP/REST API
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                    FastAPI 后端 (Port: 8000)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     API 层 (endpoints/)                   │  │
│  │  health  qa  reviews  imports  standards  prompts  audit │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   服务层 (services/)                      │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │  │
│  │  │ rag_pipeline   │  │    ingest      │  │   batch    │ │  │
│  │  │  双轨RAG编排   │  │   文档导入     │  │  批量处理  │ │  │
│  │  └────────────────┘  └────────────────┘  └────────────┘ │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  客户端层 (clients/)                      │  │
│  │  ┌────────────────┐              ┌────────────────┐     │  │
│  │  │ ragflow_client │              │   llm_client   │     │  │
│  │  │  向量检索封装  │              │   LLM 统一接口 │     │  │
│  │  └────────────────┘              └────────────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                      │               │
│  ┌────────────────────────┴──────────┐          │               │
│  │       数据访问层 (db/)             │          │               │
│  │  • session.py - 异步会话          │          │               │
│  │  • models.py  - ORM 模型          │          │               │
│  └───────────────────────────────────┘          │               │
└─────────────────────────────────────────────────┼───────────────┘
                           │                      │
┌──────────────────────────┴──────────┐  ┌────────┴─────────────┐
│         MySQL 8.4                    │  │   外部 LLM 服务      │
│  • 用户与权限                        │  │  ┌─────────────────┐│
│  • 知识文档元数据                    │  │  │  Qwen-max       ││
│  • 标准答案库                        │  │  │  (阿里云)       ││
│  • 问题与答案                        │  │  └─────────────────┘│
│  • 审核任务                          │  │  ┌─────────────────┐│
│  • 审计日志                          │  │  │  DeepSeek       ││
│  Port: 3306                          │  │  │  (备选)         ││
└──────────────────────────────────────┘  │  └─────────────────┘│
                                          └─────────────────────┘
┌──────────────────────────────────────┐
│       RAGFlow v0.21.0                │
│  ┌──────────────────────────────────┐│
│  │  文档解析                        ││
│  │  • PDF/DOCX → Text              ││
│  │  • 智能切片                      ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │  向量化                          ││
│  │  • Text → Embedding             ││
│  │  • 存储到 Elasticsearch         ││
│  └──────────────────────────────────┘│
│  ┌──────────────────────────────────┐│
│  │  向量检索                        ││
│  │  • 语义相似度搜索                ││
│  │  • Rerank 重排序                ││
│  └──────────────────────────────────┘│
│  Web: 80  |  API: 9380               │
└──────────────────────────────────────┘
```

---

## 数据流向

### 1. 文档导入流程

```
用户上传 ZIP
    ↓
前端 (Vue3/Streamlit)
    ↓
POST /api/v1/imports/knowledge-a-zip
    ↓
Backend: imports.py
    ↓
保存到 /app/storage/uploads/
    ↓
创建 ImportBatch 记录
    ↓
异步任务: ingest.process_knowledge_a_zip()
    ↓
解压 ZIP → 遍历 PDF/DOCX
    ↓
┌────────────────────────────────────────┐
│  并行处理每个文档                       │
│  ┌──────────────┐    ┌──────────────┐ │
│  │  保存元数据  │    │  上传到      │ │
│  │  到 MySQL    │    │  RAGFlow     │ │
│  └──────────────┘    └──────────────┘ │
└────────────────────────────────────────┘
    ↓
触发 RAGFlow 解析
    ↓
RAGFlow: 解析 → 切片 → 向量化 → 存储
    ↓
状态: Pending → Processing → Completed
```

### 2. 问答生成流程

```
用户提问
    ↓
POST /api/v1/qa/answer
    ↓
RAGPipeline.answer()
    ↓
┌────────────────────────────────────────┐
│  并发检索（asyncio.gather）             │
│  ┌──────────────┐    ┌──────────────┐ │
│  │  轨道A检索   │    │  轨道B检索   │ │
│  │  RAGFlow API │    │  RAGFlow API │ │
│  │  top_k=5     │    │  top_k=5     │ │
│  └──────────────┘    └──────────────┘ │
│        ↓                    ↓          │
│  [证据片段A]          [标准答案B]      │
└────────────────────────────────────────┘
    ↓                     ↓
生成初稿                对齐分析
    ↓                     ↓
LLM (Qwen-max)        计算相似度
    ↓                     ↓
基于A轨证据 + Prompt   判断对齐模式
    ↓                     ↓
初稿文本              强/弱/自由
    ↓                     ↓
┌────────────────────────────────────────┐
│            对齐与冲突检测               │
│  • 相似度 ≥ 0.8: 强约束对齐            │
│  • 0.6 ≤ 相似度 < 0.8: 弱约束对齐      │
│  • 相似度 < 0.6: 自由生成              │
│  • 检测冲突: 免责声明/术语/时间窗口    │
└────────────────────────────────────────┘
    ↓
返回结果
{
  initial: "初稿",
  aligned: "对齐后",
  evidence_a: {...},
  evidence_b: {...},
  alignment: {mode, conflicts, ...}
}
    ↓
创建审核任务 (可选)
    ↓
审核工作台
```

### 3. 审核流程

```
审核任务创建
    ↓
ReviewTask (status=pending)
    ↓
审核人员查看
    ↓
Streamlit 审核工作台
    ↓
查看初稿、对齐后、证据、冲突
    ↓
审核决策
    ↓
┌─────────────────────────────────────┐
│  审核操作                            │
│  ┌─────────┐  ┌─────────┐  ┌──────┐│
│  │  通过   │  │  退回   │  │ 拒绝 ││
│  │ approve │  │ request │  │reject││
│  │         │  │ changes │  │      ││
│  └────┬────┘  └────┬────┘  └──┬───┘│
└───────┼────────────┼──────────┼────┘
        ↓            ↓          ↓
    发布使用      重新生成    归档
        │            │          │
        └────────────┴──────────┘
                     │
            ┌────────┴────────┐
            │   可选: Promote  │
            │  升级为标准答案  │
            └─────────────────┘
                     ↓
            StandardAnswer 新版本
                     ↓
            加入轨道B知识库
```

---

## 核心组件说明

### 1. RAG Pipeline (rag_pipeline.py)

**职责**：双轨 RAG 的核心编排逻辑

**关键方法**：
- `retrieve_a_b()`: 并发检索轨道A和B
- `generate_initial_from_a()`: 基于A轨生成初稿
- `align_with_b()`: 基于B轨对齐校验
- `_extract_conflicts()`: 冲突检测
- `answer()`: 完整问答流程

**扩展点**：
- 增强冲突检测规则
- 添加多路召回策略
- 实现缓存机制

### 2. Ingest Service (ingest.py)

**职责**：文档导入和 RAGFlow 集成

**支持的导入模式**：
1. **纯 ZIP 模式**：自动从文件名提取标题
2. **CSV 模式**：从 CSV 读取元数据
3. **混合模式**：CSV 元数据 + ZIP 文件包

**关键方法**：
- `process_knowledge_a_zip()`: 处理 ZIP 文件
- `process_knowledge_a_file()`: 处理 CSV 文件
- `process_knowledge_a_hybrid()`: 混合模式
- `process_standards_b_file()`: 处理标准答案
- `_update_batch()`: 更新批次状态

### 3. RAGFlow Client (ragflow_client.py)

**职责**：封装 RAGFlow v0.21.0 API

**关键方法**：
- `upload_document()`: 上传文档到 dataset
- `parse_document()`: 触发文档解析
- `query()`: 向量检索
- `_normalize_chunks()`: 结果归一化

**API 端点**：
- 上传: `POST /api/v1/datasets/{dataset_id}/documents`
- 解析: `POST /api/v1/datasets/{dataset_id}/chunks`
- 查询: `POST /api/v1/datasets/{dataset_id}/retrieval` (待确认)

### 4. LLM Client (llm_client.py)

**职责**：统一的 LLM 调用接口

**支持的提供商**：
- Qwen (阿里云通义千问)
- DeepSeek
- OpenAI

**自动配置**：
- 根据 `LLM_PROVIDER` 自动选择 base_url
- 根据提供商自动选择对应的 API Key
- 统一的 chat completion 接口

---

## 数据模型关系

```
User (用户)
  │
  ├─── audit_logs (审计日志)
  │
  └─── review_tasks.assignee (分配的审核任务)

PromptTemplate (Prompt模板)
  │
  └─── questions (使用该模板的问题)

ImportBatch (导入批次)
  │
  └─── knowledge_docs (该批次的文档)

StandardAnswer (标准答案主题)
  │
  └─── standard_answer_versions (版本列表)
       ├─── version 1
       ├─── version 2
       └─── version 3

Question (问题)
  │
  ├─── generated_answers (生成的答案)
  │
  └─── review_tasks (审核任务)

GeneratedAnswer (生成答案)
  │
  └─── review_tasks (对应的审核任务)

ReviewTask (审核任务)
  ├─── question (关联问题)
  ├─── generated_answer (关联答案)
  └─── assignee (审核人)
```

---

## 配置管理

### 配置优先级

```
1. 环境变量 (docker-compose.yml)
   ↓
2. .env 文件 (backend/.env)
   ↓
3. 默认值 (backend/app/core/config.py)
```

### 配置类 (Settings)

```python
class Settings(BaseSettings):
    # 数据库
    mysql_user: str = "root"
    mysql_password: str = "password"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_db: str = "ir_rag"
    
    # RAGFlow
    ragflow_base_url: str = "http://localhost:7860"
    ragflow_api_key: str = ""
    
    # LLM
    llm_provider: str = "qwen"
    llm_model: str = "qwen-max"
    qwen_api_key: str = ""
    deepseek_api_key: str = ""
    
    # 对齐阈值
    alignment_strong_threshold: float = 0.8
    alignment_weak_threshold: float = 0.6
    
    # 其他
    storage_base_dir: str = "./storage"
    cors_allow_origins: List[str] = ["*"]
```

---

## 安全考虑

### 当前实现

1. **CORS 配置**：允许指定来源
2. **API Key 认证**：RAGFlow 和 LLM 使用 Bearer Token
3. **审计日志**：记录关键操作
4. **用户标识**：通过 `X-User-Email` 头传递

### 生产环境建议

1. **认证授权**
   - 集成企业 SSO (OIDC/SAML)
   - 实现细粒度 RBAC
   - JWT Token 认证

2. **数据安全**
   - 敏感字段加密
   - PII 数据脱敏
   - 数据访问审计

3. **网络安全**
   - HTTPS/TLS 加密
   - 速率限制
   - 防 DDoS

4. **合规性**
   - 数据留存策略
   - 访问控制列表
   - 定期安全审计

---

## 性能优化

### 已实现

1. **异步处理**
   - 所有 I/O 操作使用 async/await
   - 并发检索轨道A和B
   - 异步数据库操作

2. **重试机制**
   - RAGFlow API 调用自动重试（3次）
   - LLM API 调用自动重试（3次）
   - 指数退避策略

3. **连接池**
   - HTTPx 异步客户端复用
   - SQLAlchemy 连接池

### 优化建议

1. **缓存策略**
   ```python
   # 语义缓存
   - 问题归一化 + 向量相似度
   - Redis 缓存常见问答
   - LRU 缓存 Prompt 模板
   ```

2. **批量优化**
   ```python
   # 批量检索
   - 合并相似问题的检索请求
   - 批量调用 LLM API
   - 批量数据库插入
   ```

3. **索引优化**
   ```sql
   -- 添加索引
   CREATE INDEX idx_questions_status ON questions(status);
   CREATE INDEX idx_review_tasks_status ON review_tasks(status);
   CREATE INDEX idx_knowledge_docs_category ON knowledge_docs(category);
   ```

---

## 监控与观测

### 日志

**Loguru 配置** (backend/app/core/logging.py):
- 彩色终端输出
- 日志文件轮转
- 结构化日志（JSON）

**日志级别**:
- DEBUG: 详细调试信息
- INFO: 关键操作记录
- WARNING: RAGFlow 上传失败等
- ERROR: 系统错误

### 健康检查

```bash
# 后端健康
curl http://localhost:8000/api/v1/health

# 返回示例
{
  "status": "ok",
  "db": true
}
```

### 指标监控

```bash
# 系统指标
curl http://localhost:8000/api/v1/metrics

# 返回示例
{
  "total_questions": 100,
  "reviewed_count": 80,
  "approval_rate": 75.0,
  "standard_answers_count": 20,
  "review_status_distribution": {
    "pending": 10,
    "approved": 60,
    "rejected": 10,
    "needs_revision": 10
  }
}
```

---

## 扩展指南

### 添加新的对齐规则

编辑 `backend/app/services/rag_pipeline.py`:

```python
def _extract_conflicts(self, mode: str, draft: str, b_chunks: List[Dict]) -> List[Dict]:
    conflicts = []
    
    # 现有规则
    if mode == "strong":
        if "免责声明" not in draft:
            conflicts.append({
                "type": "missing_disclaimer",
                "message": "缺少免责声明段落"
            })
    
    # 新增规则示例
    if "具体数据" in draft and "来源:" not in draft:
        conflicts.append({
            "type": "missing_source",
            "message": "提及具体数据但未标注来源"
        })
    
    return conflicts
```

### 集成新的 LLM 提供商

编辑 `backend/app/clients/llm_client.py`:

```python
# 添加新提供商配置
if self.provider == "your_llm":
    self.base_url = "https://api.your-llm.com/v1"
elif self.provider == "qwen":
    self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
# ...
```

### 添加新的文档类型

编辑 `backend/app/models/enums.py`:

```python
class DocCategory(str, Enum):
    ANNOUNCEMENT = "announcement"
    RESEARCH = "research"
    FAQ = "faq"
    POLICY = "policy"
    YOUR_NEW_TYPE = "your_new_type"  # 新增
```

---

## 测试

### 单元测试（待实现）

```bash
cd backend
pytest tests/ -v
```

### 集成测试

```bash
# 测试健康检查
curl http://localhost:8000/api/v1/health

# 测试问答
curl -X POST http://localhost:8000/api/v1/qa/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "测试问题",
    "kb_a_id": "xxx",
    "kb_b_id": "xxx"
  }'
```

### 端到端测试（待实现）

使用 Playwright 进行前端 E2E 测试

---

**维护者**: IR Team  
**创建日期**: 2024-10-20  
**最后更新**: 2025-10-21

