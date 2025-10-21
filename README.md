# IR_RAG - 双轨 RAG 的 IR 问答系统

本项目为医药公司 IR 场景构建的前后端分离问答系统，特点是与 RAGFlow 集成的“双轨 RAG”：
- 轨道A：公司基础信息/公告/研发等事实性知识，直接用于生成初稿
- 轨道B：标准回答库（版本化、可配置强/弱约束），用于对齐与合规校验

支持：批量导入（A/B/问题）、单问即答、审核工作台（通过/退回/拒绝/升级为标准回答）、Prompt 模板管理、审计与基础指标。


## 技术栈与运行

- 后端：FastAPI + SQLAlchemy(Async) + Alembic + MySQL 8.4 + httpx + Loguru
- 前端：Vue3 + Vite + Element Plus
- 向量检索/解析：RAGFlow v0.21.0（已对接客户端与接口）
- LLM：DeepSeek（占位客户端，默认走 chat-completion API）
- 容器：Docker Compose（带健康检查）

启动（Docker Desktop）：
```bash
docker compose build && docker compose up -d
# 前端 http://localhost:5173
# 后端 Swagger http://localhost:8000/docs
# Adminer http://localhost:8080 （Server=mysql, User=ir, Password=ir_password, DB=ir_rag）
```


## 环境变量

- backend/.env（示例见 backend/.env.example）
  - MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DB
  - RAGFLOW_BASE_URL（默认 http://host.docker.internal:7860）
  - RAGFLOW_API_KEY（如启用）
  - DEEPSEEK_API_KEY（如直连）
  - STORAGE_BASE_DIR（默认 /app/storage）
  - CORS_ALLOW_ORIGINS
- 前端默认通过 vite 代理将 /api 指向后端 8000 端口（Docker 镜像使用 Nginx 提供静态页）。


## 目录结构（关键）

```text
backend/
  app/
    api/
      v1/
        endpoints/
          health.py          # 健康检查
          qa.py              # 单问即答：并查A/B
          imports.py         # 批量导入：A/B/问题 + 批次列表
          standards.py       # 标准回答：promote 保存为版本
          reviews.py         # 审核工作台：列表/详情/通过/退回/拒绝
          prompts.py         # Prompt 模板：列表/创建/新版本/编辑
          audit.py           # 审计日志列表
          metrics.py         # 基础指标
        routes.py            # v1 路由汇总
      deps.py                # 公共依赖：当前用户解析、审计写入
    clients/
      ragflow_client.py     # RAGFlow 客户端（v0.21.0，query 结果归一化）
      deepseek_client.py    # DeepSeek 客户端（占位）
    core/
      config.py             # 配置与 env 解析
      logging.py            # 日志
    db/
      session.py            # Async engine & Session
    models/
      enums.py              # 枚举
      models.py             # ORM 模型（用户/Prompt/A/B/问题/生成/审核/导入/审计）
    schemas/
      common.py
    services/
      rag_pipeline.py       # RAG 编排（A/B 并发检索；A生成，B对齐）
      ingest.py             # A/B 导入解析、入库、RAGFlow上传；批次状态
      batch_processor.py    # 批量问题入库与异步生成
    main.py                 # FastAPI 入口 + /samples 静态挂载
  alembic.ini
  alembic/
    env.py
    versions/
      20251020_0001_init.py # 初始迁移
  requirements.txt
  Dockerfile
  entrypoint.sh
frontend/
  src/
    views/
      QAView.vue            # 单问即答（并查A/B）
      ImportsView.vue       # 批量导入与模板下载
      StandardsView.vue     # 标准回答（手动录入/Promote）
      PromptsView.vue       # Prompt 模板管理
      ReviewsView.vue       # 审核工作台（初稿/对齐/冲突/操作/Promote）
    api.ts                  # axios 实例
    App.vue, main.ts
  package.json, vite.config.ts, Dockerfile
samples/
  import_templates/         # CSV 模板（A/B/问题）
README.md
Docker-compose.yml
```


## 双轨 RAG 流程（核心）

1) 问题规整（可选）与路由
2) 并发检索
   - A：公告/研报/FAQ/政策/披露等分类，召回证据片段
   - B：标准回答库（版本化），召回相似问与模板（含强/弱约束）
3) 初稿生成（以A为主），由 DeepSeek/或 RAGFlow 产出
4) 对齐（以B为约束）：
   - 相似度≥强阈值：强约束（模板与措辞严格对齐）
   - 相似度≥弱阈值：弱约束（保留事实初稿，按模板补齐结构/声明）
   - 否则：自由模式（依赖A初稿）
   - 冲突检测（占位实现，已预留结构）：免责声明缺失、术语/口径不一致、时间窗口不一致
5) 合规拦截：生成前/后双层关键字与规则校验（可扩展）
6) 审核：初稿+对齐+证据+冲突 -> 通过/退回/拒绝；优秀回答一键升级为标准回答（B库新版本）


## 主要 API（后端）

- 健康：GET `/api/v1/health`
- 单问即答：POST `/api/v1/qa/answer`
  - body: { question, prompt, kb_a_id, kb_b_id, top_k_a, top_k_b }
- 导入知识库A（三种模式）
  - POST `/api/v1/imports/knowledge-a?kb_a_id=...`（CSV/Excel 列：title, category, source_path, source_url, disclosure_date。适用于文件已在服务器的场景）
  - POST `/api/v1/imports/knowledge-a-zip?kb_a_id=...&default_category=announcement`（**纯ZIP模式，最简单**：只传 ZIP 包含 PDF/DOCX，自动从文件名提取标题）
  - POST `/api/v1/imports/knowledge-a-hybrid?kb_a_id=...`（**混合模式，最完整**：同时上传 CSV 元数据 + ZIP 文件包，CSV 列：title, category, filename, source_url, disclosure_date, description。ZIP 内包含 PDF/DOCX，通过 filename 列匹配）
- 导入其它
  - POST `/api/v1/imports/standards-b`（列：topic_key, content, strong_constraint, effective_from, effective_to, description）
  - POST `/api/v1/imports/questions?kb_a_id=...&kb_b_id=...&generate=true&prompt=...`（列：question）
  - GET `/api/v1/imports/batches` 批次列表（状态：queued/processing/completed/failed）
- 标准回答（B）
  - POST `/api/v1/standards/promote`（topic_key、content、强约束、有效窗口）
- 审核工作台
  - GET `/api/v1/reviews?status=...`
  - GET `/api/v1/reviews/{task_id}`
  - POST `/api/v1/reviews/{task_id}/approve|request_changes|reject`
- Prompt 模板
  - GET `/api/v1/prompts`
  - POST `/api/v1/prompts`（X-User-Email 审计）
  - POST `/api/v1/prompts/{name}/new_version`
  - PATCH `/api/v1/prompts/{prompt_id}`
- 审计与指标
  - GET `/api/v1/audit`
  - GET `/api/v1/metrics`
- 静态模板下载：`/samples`（容器内拷贝 samples/import_templates）


## 数据库（MySQL 8.4）

- users, audit_logs
- prompt_templates（版本化按 name + version）
- knowledge_docs（轨道A，含 category/source/meta/disclosure_date）
- standard_answers（轨道B主题头）/standard_answer_versions（版本窗与强/弱约束）
- questions, generated_answers（初稿/对齐稿/证据/对齐摘要），review_tasks
- import_batches（导入批次：type/status/file_path/metadata）

Alembic 初始迁移：`backend/alembic/versions/20251020_0001_init.py`


## RAGFlow 对接

- 客户端：`app/clients/ragflow_client.py`，统一 query 返回：
  ```json
  { "chunks": [ { "text": "...", "score": 0.85, "metadata": { … } } ] }
  ```
- 上传：`upload_document(file_path, kb_id, metadata)`（根据 v0.21.0 实际 API 调整）


## 常见操作

- 单问即答（Swagger 调用 `/api/v1/qa/answer`）
- 批量导入（前端“批量导入”页，或 Swagger）
- 审核任务处理（前端“审核工作台”）
- 标注为标准回答（审核页内 Promote，或直接调用 API）
- Prompt 管理（前端 Prompt 页；请求头可带 `X-User-Email` 记录审计）


## 约定与扩展点

- 强/弱阈值在 env 中配置：`alignment_strong_threshold` / `alignment_weak_threshold`
- 冲突检测目前为占位实现（缺少“免责声明”等），可扩展术语/口径/时间窗口等规则
- DeepSeek 与 RAGFlow 的实际 API Schema 可根据生产部署进一步对齐
- 对象存储可从本地目录平滑迁移到 MinIO/云对象存储
- 权限与 SSO 可替换 `X-User-Email` 头为企业内网统一认证


## 运行时健康与数据卷

- docker-compose 对 MySQL 与后端设置 healthcheck
- 数据卷：
  - `mysql_data` 持久化 MySQL 数据
  - `backend_storage` 持久化 `/app/storage`（上传与中间产物）


## 面向 AI Coding 工具的上下文要点

- 业务流代码集中在 `backend/app/services/` 与 `backend/app/api/v1/endpoints/`
- 若需扩展对齐规则，请修改 `services/rag_pipeline.py` 的 `_extract_conflicts` 与 `align_with_b`
- 导入管线入口在 `endpoints/imports.py`，状态与持久化在 `services/ingest.py`
- 前端页面已分视图模块，调用统一的 `src/api.ts`；可在对应视图新增字段校验或 UI 细化
- 如需新增实体，请先补充 ORM 与 Alembic 迁移，再增 API/服务层逻辑


## 待优化与 Roadmap

- 对齐规则与合规
  - 扩展冲突检测：术语词典、口径一致性（财务期间/口径）、时间窗口一致性、来源必引校验
  - 生成前后双层拦截的规则中心化（规则版本化、按场景启用/禁用、灰度发布）
- RAGFlow 集成细化
  - 按 v0.21.0 实际 API Schema 补齐：检索字段、上传参数、管线配置回读
  - 为 A/B 知识库增加多索引/多路召回与投票融合（RRF/MaxSim）
- LLM 能力
  - DeepSeek 流式与函数调用（工具调用）
  - 成本/延迟优化：缓存（问题归一化语义缓存）、重试/降级策略、批处理并发
- 批量与队列
  - 引入显式任务队列（Celery/RQ）与重试、幂等（基于文件hash/批次ID）
  - 导入批次的进度明细与错误导出（行级错误报告）
- 安全与权限
  - 集成企业 SSO（OIDC/SAML），细粒度 RBAC 与数据域隔离
  - 请求签名、速率限制与防滥用；审计落盘与集中化（对接 SIEM）
- 数据与隐私
  - PII/敏感字段脱敏与最小化持久化；日志/样本清理周期化
  - 对象存储替换为 MinIO/云厂商，并提供直传（Pre-signed URL）
- 观测与评估
  - 指标：召回质量（命中率/覆盖率）、一致性分、合规命中、审核通过率、耗时/成本
  - Tracing（OpenTelemetry）与集中日志（ELK/CloudWatch）
- 前端体验
  - 审核工作台：证据高亮对齐、差异可视化、术语建议替换、快捷键
  - 导入向导：模板下载/样例预览、字段校验、错误行回填
- 工程化
  - CI/CD、单元/集成测试、端到端测试（Playwright）
  - Alembic 自动生成/回滚策略、蓝绿/灰度发布脚本
- 架构与扩展
  - 多租户（Schema/Row-Level Security）
  - 多语言与时区、国际化 i18n
  - 可插拔向量库（FAISS/Chroma/PGVector/Weaviate）与召回策略切换
