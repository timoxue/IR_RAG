import streamlit as st
import requests
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

# 配置
BACKEND_API = os.getenv("BACKEND_API_URL", "http://localhost:8000")
USER_EMAIL = os.getenv("USER_EMAIL", "ir@example.com")

# 页面配置
st.set_page_config(
    page_title="IR 问答审核系统",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .answer-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
    }
    .evidence-box {
        padding: 0.5rem;
        border-left: 3px solid #1f77b4;
        margin: 0.5rem 0;
        background-color: #e8f4f8;
    }
    .conflict-box {
        padding: 0.5rem;
        border-left: 3px solid #ff4b4b;
        margin: 0.5rem 0;
        background-color: #ffe8e8;
    }
</style>
""", unsafe_allow_html=True)


# API 调用函数
def api_get(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """调用后端 GET API"""
    try:
        response = requests.get(f"{BACKEND_API}{endpoint}", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 调用失败: {e}")
        return {}


def api_post(endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
    """调用后端 POST API"""
    try:
        headers = {"X-User-Email": USER_EMAIL}
        response = requests.post(
            f"{BACKEND_API}{endpoint}",
            json=data,
            files=files,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 调用失败: {e}")
        return {}


# 侧边栏 - 功能选择
with st.sidebar:
    st.title("🏥 IR 问答审核系统")
    st.markdown("---")
    
    page = st.radio(
        "选择功能模块",
        ["📝 单问即答", "✅ 审核工作台", "📚 标准回答管理", "🎨 Prompt 管理", "📊 系统指标"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption(f"当前用户: {USER_EMAIL}")
    st.caption(f"后端: {BACKEND_API}")


# ========== 页面1: 单问即答 ==========
if page == "📝 单问即答":
    st.header("📝 单问即答 - 双轨 RAG")
    st.markdown("基于轨道A（事实知识）和轨道B（标准回答库）的智能问答系统")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("提问配置")
        
        kb_a_id = st.text_input("知识库 A ID", value="9d836ce6ae7c11f08b543a9883fcddc0", 
                                help="轨道A：公司公告、研报、FAQ等事实性知识库")
        kb_b_id = st.text_input("标准库 B ID", value="", 
                                help="轨道B：标准回答库，用于对齐和合规校验")
        
        question = st.text_area("问题", height=100, 
                               placeholder="例如：公司最新的研发管线进展如何？")
        
        with st.expander("高级选项", expanded=False):
            prompt = st.text_area("自定义 Prompt", height=100, 
                                 placeholder="可选，自定义生成指令")
            col_a, col_b = st.columns(2)
            with col_a:
                top_k_a = st.number_input("轨道A检索数量", min_value=1, max_value=20, value=5)
            with col_b:
                top_k_b = st.number_input("轨道B检索数量", min_value=1, max_value=20, value=5)
        
        if st.button("🚀 提问", type="primary", use_container_width=True):
            if not question:
                st.warning("请输入问题")
            elif not kb_a_id:
                st.warning("请输入知识库 A ID")
            else:
                with st.spinner("AI 正在思考..."):
                    result = api_post("/api/v1/qa/answer", {
                        "question": question,
                        "prompt": prompt or "",
                        "kb_a_id": kb_a_id,
                        "kb_b_id": kb_b_id or kb_a_id,  # 如果B为空，使用A
                        "top_k_a": top_k_a,
                        "top_k_b": top_k_b
                    })
                    
                    if result:
                        st.session_state.qa_result = result
    
    with col2:
        st.subheader("系统说明")
        st.info("""
        **双轨 RAG 机制**
        
        🔵 **轨道A**: 事实知识库
        - 公司公告
        - 研发报告  
        - FAQ文档
        
        🟢 **轨道B**: 标准回答库
        - 版本化标准答案
        - 强/弱约束配置
        - 合规校验规则
        
        **生成流程**:
        1. 并发检索 A/B 轨道
        2. 基于 A 生成初稿
        3. 基于 B 对齐校验
        4. 输出最终答案
        """)
    
    # 显示结果
    if "qa_result" in st.session_state:
        result = st.session_state.qa_result
        
        st.markdown("---")
        st.subheader("📊 生成结果")
        
        tab1, tab2, tab3 = st.tabs(["初稿 (A轨)", "对齐后 (B轨)", "证据与对齐信息"])
        
        with tab1:
            st.markdown("### 初稿（基于事实知识）")
            st.markdown(f'<div class="answer-box">{result.get("initial", "")}</div>', 
                       unsafe_allow_html=True)
        
        with tab2:
            st.markdown("### 对齐后（经过标准库校验）")
            st.markdown(f'<div class="answer-box">{result.get("aligned", "")}</div>', 
                       unsafe_allow_html=True)
            
            # 对齐信息
            alignment = result.get("alignment", {})
            if alignment:
                st.markdown("#### 对齐分析")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("对齐模式", alignment.get("mode", "unknown").upper())
                with col_b:
                    st.metric("最高相似度", f"{alignment.get('max_score', 0):.2f}")
                with col_c:
                    mode = alignment.get("mode", "")
                    if mode == "strong":
                        st.success("🔒 强约束对齐")
                    elif mode == "weak":
                        st.info("🔓 弱约束对齐")
                    else:
                        st.warning("🆓 自由生成")
                
                # 冲突检测
                conflicts = alignment.get("conflicts", [])
                if conflicts:
                    st.markdown("#### ⚠️ 检测到的冲突")
                    for conflict in conflicts:
                        st.markdown(f'<div class="conflict-box"><strong>{conflict.get("type")}</strong>: {conflict.get("message")}</div>', 
                                   unsafe_allow_html=True)
        
        with tab3:
            st.markdown("### 证据来源")
            
            col_ev_a, col_ev_b = st.columns(2)
            
            with col_ev_a:
                st.markdown("#### 📘 轨道A证据")
                evidence_a = result.get("evidence_a", {})
                chunks_a = evidence_a.get("chunks", [])
                for i, chunk in enumerate(chunks_a):
                    with st.expander(f"证据 {i+1} (相似度: {chunk.get('score', 0):.3f})"):
                        st.text(chunk.get("text", ""))
                        if chunk.get("metadata"):
                            st.json(chunk.get("metadata"))
            
            with col_ev_b:
                st.markdown("#### 📗 轨道B证据")
                evidence_b = result.get("evidence_b", {})
                chunks_b = evidence_b.get("chunks", [])
                for i, chunk in enumerate(chunks_b):
                    with st.expander(f"标准答案 {i+1} (相似度: {chunk.get('score', 0):.3f})"):
                        st.text(chunk.get("text", ""))
                        if chunk.get("metadata"):
                            st.json(chunk.get("metadata"))


# ========== 页面2: 审核工作台 ==========
elif page == "✅ 审核工作台":
    st.header("✅ 审核工作台")
    st.markdown("审核 AI 生成的答案，确保质量与合规")
    
    # 过滤器
    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
    with col_filter1:
        status_filter = st.selectbox(
            "状态过滤",
            ["全部", "待审核", "需修订", "已通过", "已拒绝"],
            index=1
        )
    with col_filter2:
        if st.button("🔄 刷新列表", use_container_width=True):
            st.rerun()
    with col_filter3:
        auto_refresh = st.checkbox("自动刷新", value=False)
    
    # 获取任务列表
    status_map = {
        "全部": "",
        "待审核": "pending",
        "需修订": "needs_revision",
        "已通过": "approved",
        "已拒绝": "rejected"
    }
    
    tasks_response = api_get("/api/v1/reviews", 
                            params={"status": status_map[status_filter]} if status_filter != "全部" else None)
    tasks = tasks_response.get("tasks", [])
    
    if not tasks:
        st.info("📭 暂无审核任务")
    else:
        st.success(f"找到 {len(tasks)} 个任务")
        
        # 任务列表和详情（左右布局）
        col_list, col_detail = st.columns([1, 2])
        
        with col_list:
            st.subheader("📋 任务列表")
            
            # 初始化选中的任务
            if "selected_task_id" not in st.session_state:
                st.session_state.selected_task_id = None
            
            # 显示任务列表
            for task in tasks:
                task_id = task.get("id")
                status = task.get("status", "")
                question_id = task.get("question_id", "")
                
                # 状态标签
                status_emoji = {
                    "pending": "⏳",
                    "needs_revision": "📝",
                    "approved": "✅",
                    "rejected": "❌"
                }.get(status, "❓")
                
                # 任务按钮
                if st.button(
                    f"{status_emoji} 任务 #{task_id} | Q{question_id}",
                    key=f"task_{task_id}",
                    use_container_width=True
                ):
                    st.session_state.selected_task_id = task_id
                    st.rerun()
        
        with col_detail:
            if st.session_state.selected_task_id:
                task_id = st.session_state.selected_task_id
                
                # 获取任务详情
                detail = api_get(f"/api/v1/reviews/{task_id}")
                
                if detail:
                    st.subheader(f"📄 任务 #{task_id} 详情")
                    
                    # 问题
                    st.markdown("### 📌 问题")
                    st.info(detail.get("question", ""))
                    
                    # 答案对比
                    st.markdown("### 💬 答案对比")
                    col_init, col_aligned = st.columns(2)
                    
                    with col_init:
                        st.markdown("**初稿 (轨道A)**")
                        st.markdown(f'<div class="answer-box">{detail.get("initial_answer", "")}</div>', 
                                   unsafe_allow_html=True)
                    
                    with col_aligned:
                        st.markdown("**对齐后 (轨道B)**")
                        st.markdown(f'<div class="answer-box">{detail.get("aligned_answer", "")}</div>', 
                                   unsafe_allow_html=True)
                    
                    # 对齐信息
                    alignment = detail.get("alignment", {})
                    if alignment:
                        st.markdown("### 🔍 对齐分析")
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("对齐模式", alignment.get("mode", "").upper())
                        with col_m2:
                            st.metric("相似度", f"{alignment.get('max_score', 0):.3f}")
                        with col_m3:
                            st.metric("强阈值", f"{alignment.get('strong', 0):.2f}")
                        
                        # 冲突
                        conflicts = alignment.get("conflicts", [])
                        if conflicts:
                            st.markdown("#### ⚠️ 检测到的冲突")
                            for conflict in conflicts:
                                st.markdown(f'<div class="conflict-box"><strong>{conflict.get("type")}</strong>: {conflict.get("message")}</div>', 
                                           unsafe_allow_html=True)
                    
                    # 审核操作
                    st.markdown("---")
                    st.markdown("### ✍️ 审核操作")
                    
                    comments = st.text_area("审核意见", height=100, key="review_comments")
                    
                    col_act1, col_act2, col_act3 = st.columns(3)
                    
                    with col_act1:
                        if st.button("✅ 通过", type="primary", use_container_width=True):
                            result = api_post(f"/api/v1/reviews/{task_id}/approve", 
                                            {"comments": comments})
                            if result:
                                st.success("✅ 审核通过！")
                                st.session_state.selected_task_id = None
                                st.rerun()
                    
                    with col_act2:
                        if st.button("📝 退回修订", use_container_width=True):
                            result = api_post(f"/api/v1/reviews/{task_id}/request_changes", 
                                            {"comments": comments})
                            if result:
                                st.warning("📝 已退回修订")
                                st.session_state.selected_task_id = None
                                st.rerun()
                    
                    with col_act3:
                        if st.button("❌ 拒绝", use_container_width=True):
                            result = api_post(f"/api/v1/reviews/{task_id}/reject", 
                                            {"comments": comments})
                            if result:
                                st.error("❌ 已拒绝")
                                st.session_state.selected_task_id = None
                                st.rerun()
                    
                    # 升级为标准回答
                    st.markdown("---")
                    st.markdown("### ⭐ 升级为标准回答")
                    
                    with st.form("promote_form"):
                        topic_key = st.text_input("主题键 (Topic Key)", 
                                                 placeholder="例如：rd_pipeline_update")
                        strong_constraint = st.checkbox("强约束", value=False,
                                                       help="强约束：严格按模板对齐；弱约束：保留事实，按模板补齐")
                        
                        submitted = st.form_submit_button("⭐ 保存为标准回答", type="primary")
                        
                        if submitted and topic_key:
                            content = detail.get("aligned_answer") or detail.get("initial_answer")
                            result = api_post("/api/v1/standards/promote", {
                                "topic_key": topic_key,
                                "content": content,
                                "strong_constraint": strong_constraint
                            })
                            if result:
                                st.success(f"⭐ 已保存为标准回答: {topic_key}")
            else:
                st.info("👈 请从左侧列表选择一个任务")


# ========== 页面3: 标准回答管理 ==========
elif page == "📚 标准回答管理":
    st.header("📚 标准回答库")
    st.markdown("管理标准回答模板，支持版本化和强/弱约束配置")
    
    tab1, tab2 = st.tabs(["➕ 新建标准回答", "📋 查看列表"])
    
    with tab1:
        st.subheader("创建新的标准回答")
        
        with st.form("create_standard"):
            topic_key = st.text_input("主题键 (Topic Key)", 
                                     placeholder="例如：share_buyback_policy")
            content = st.text_area("标准答案内容", height=200,
                                  placeholder="输入标准回答的完整内容...")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                strong_constraint = st.checkbox("强约束", value=False)
            with col_c2:
                description = st.text_input("描述（可选）")
            
            submitted = st.form_submit_button("💾 保存", type="primary")
            
            if submitted:
                if not topic_key or not content:
                    st.warning("请填写主题键和内容")
                else:
                    result = api_post("/api/v1/standards/promote", {
                        "topic_key": topic_key,
                        "content": content,
                        "strong_constraint": strong_constraint,
                        "description": description
                    })
                    if result:
                        st.success("✅ 标准回答已保存")
    
    with tab2:
        st.info("💡 标准回答列表功能待实现 - 可通过数据库管理工具查看")


# ========== 页面4: Prompt 管理 ==========
elif page == "🎨 Prompt 管理":
    st.header("🎨 Prompt 模板管理")
    st.markdown("管理问答生成的提示词模板，支持版本化")
    
    # 获取模板列表
    prompts = api_get("/api/v1/prompts")
    
    col_list, col_edit = st.columns([1, 2])
    
    with col_list:
        st.subheader("📋 模板列表")
        
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
        
        if prompts:
            for prompt in prompts:
                prompt_id = prompt.get("id")
                name = prompt.get("name")
                version = prompt.get("version")
                is_active = prompt.get("is_active")
                
                status_icon = "✅" if is_active else "⏸️"
                
                if st.button(f"{status_icon} {name} v{version}", key=f"prompt_{prompt_id}"):
                    st.session_state.selected_prompt = prompt
                    st.rerun()
    
    with col_edit:
        st.subheader("✏️ 编辑模板")
        
        # 新建表单
        with st.form("prompt_form"):
            name = st.text_input("模板名称", value=st.session_state.get("selected_prompt", {}).get("name", ""))
            is_active = st.checkbox("启用", value=st.session_state.get("selected_prompt", {}).get("is_active", True))
            content = st.text_area("模板内容", height=300,
                                  value=st.session_state.get("selected_prompt", {}).get("content", ""))
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                create_btn = st.form_submit_button("➕ 新建模板", type="primary")
            with col_b2:
                version_btn = st.form_submit_button("📌 创建新版本")
            
            if create_btn:
                result = api_post("/api/v1/prompts", {
                    "name": name,
                    "content": content,
                    "is_active": is_active
                })
                if result:
                    st.success("✅ 模板已创建")
                    st.rerun()
            
            if version_btn and name:
                result = api_post(f"/api/v1/prompts/{name}/new_version", {
                    "content": content,
                    "is_active": is_active
                })
                if result:
                    st.success(f"✅ 已创建 {name} 的新版本")
                    st.rerun()


# ========== 页面5: 系统指标 ==========
elif page == "📊 系统指标":
    st.header("📊 系统指标")
    st.markdown("实时监控系统运行状态和关键指标")
    
    # 获取指标
    metrics = api_get("/api/v1/metrics")
    
    if metrics:
        # 关键指标
        st.subheader("📈 关键指标")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            st.metric("总问题数", metrics.get("total_questions", 0))
        with col_m2:
            st.metric("已审核", metrics.get("reviewed_count", 0))
        with col_m3:
            st.metric("通过率", f"{metrics.get('approval_rate', 0):.1f}%")
        with col_m4:
            st.metric("标准回答数", metrics.get("standard_answers_count", 0))
        
        # 详细统计
        st.markdown("---")
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.subheader("📊 审核状态分布")
            review_stats = metrics.get("review_status_distribution", {})
            if review_stats:
                st.json(review_stats)
        
        with col_s2:
            st.subheader("📚 知识库统计")
            kb_stats = {
                "知识文档(A轨)": metrics.get("knowledge_docs_count", 0),
                "标准回答(B轨)": metrics.get("standard_answers_count", 0),
                "Prompt模板": metrics.get("prompt_templates_count", 0)
            }
            st.json(kb_stats)
    
    # 系统健康
    st.markdown("---")
    st.subheader("🏥 系统健康")
    health = api_get("/api/v1/health")
    
    if health:
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            if health.get("status") == "ok":
                st.success("✅ 后端服务正常")
            else:
                st.error("❌ 后端服务异常")
        with col_h2:
            if health.get("db"):
                st.success("✅ 数据库连接正常")
            else:
                st.error("❌ 数据库连接失败")


# 自动刷新
if page == "✅ 审核工作台" and auto_refresh:
    import time
    time.sleep(5)
    st.rerun()

