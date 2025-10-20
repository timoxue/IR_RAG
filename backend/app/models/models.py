from __future__ import annotations
from typing import Optional
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Date, ForeignKey, JSON

from app.db.session import Base
from app.models.enums import Role, DocCategory, ReviewStatus, ImportStatus


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
	name: Mapped[str] = mapped_column(String(100))
	role: Mapped[str] = mapped_column(String(20), default=Role.IR.value)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user")


class PromptTemplate(Base):
	__tablename__ = "prompt_templates"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String(100), unique=True)
	version: Mapped[int] = mapped_column(Integer, default=1)
	content: Mapped[str] = mapped_column(Text)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImportBatch(Base):
	__tablename__ = "import_batches"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	type: Mapped[str] = mapped_column(String(50))  # knowledge_a / standard_b / questions
	status: Mapped[str] = mapped_column(String(20), default=ImportStatus.QUEUED.value)
	file_path: Mapped[str] = mapped_column(String(500))
	metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
	created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	created_by: Mapped[Optional[User]] = relationship("User")


class KnowledgeDoc(Base):
	"""轨道A：公司基础信息/公告/研发等。元数据用于回溯来源。"""
	__tablename__ = "knowledge_docs"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	title: Mapped[str] = mapped_column(String(300))
	category: Mapped[str] = mapped_column(String(50), index=True)  # DocCategory
	source_path: Mapped[Optional[str]] = mapped_column(String(500))
	source_url: Mapped[Optional[str]] = mapped_column(String(500))
	disclosure_date: Mapped[Optional[date]] = mapped_column(Date)
	batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batches.id"))
	metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	batch: Mapped[Optional[ImportBatch]] = relationship("ImportBatch")


class StandardAnswer(Base):
	"""轨道B：标准回答头，按问题主题聚合；具体表述在版本表。"""
	__tablename__ = "standard_answers"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	topic_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)  # 规范化主题键
	description: Mapped[Optional[str]] = mapped_column(String(500))
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	versions: Mapped[list[StandardAnswerVersion]] = relationship(
		"StandardAnswerVersion", back_populates="standard_answer", cascade="all, delete-orphan"
	)


class StandardAnswerVersion(Base):
	__tablename__ = "standard_answer_versions"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	standard_answer_id: Mapped[int] = mapped_column(ForeignKey("standard_answers.id"))
	version: Mapped[int] = mapped_column(Integer)
	content: Mapped[str] = mapped_column(Text)  # 模板化/固定措辞
	strong_constraint: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否强约束
	effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
	effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime)
	metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	standard_answer: Mapped[StandardAnswer] = relationship("StandardAnswer", back_populates="versions")


class Question(Base):
	__tablename__ = "questions"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	asked_text: Mapped[str] = mapped_column(Text)
	normalized_text: Mapped[Optional[str]] = mapped_column(Text)
	prompt_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("prompt_templates.id"))
	status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/answered/needs_review
	metadata: Mapped[Optional[dict]] = mapped_column(JSON, default={})
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	prompt_template: Mapped[Optional[PromptTemplate]] = relationship("PromptTemplate")


class GeneratedAnswer(Base):
	__tablename__ = "generated_answers"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
	initial_answer: Mapped[str] = mapped_column(Text)  # 以A为主生成的初稿
	aligned_answer: Mapped[Optional[str]] = mapped_column(Text)  # B对齐后
	alignment_summary: Mapped[Optional[str]] = mapped_column(Text)  # 冲突/调整说明
	sources_a: Mapped[Optional[dict]] = mapped_column(JSON, default={})  # A轨证据列表
	sources_b: Mapped[Optional[dict]] = mapped_column(JSON, default={})  # B轨匹配摘要
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	question: Mapped[Question] = relationship("Question")


class ReviewTask(Base):
	__tablename__ = "review_tasks"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
	generated_answer_id: Mapped[int] = mapped_column(ForeignKey("generated_answers.id"))
	status: Mapped[str] = mapped_column(String(20), default=ReviewStatus.PENDING.value)
	assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
	comments: Mapped[Optional[str]] = mapped_column(Text)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	assignee: Mapped[Optional[User]] = relationship("User")
	question: Mapped[Question] = relationship("Question")
	generated_answer: Mapped[GeneratedAnswer] = relationship("GeneratedAnswer")


class AuditLog(Base):
	__tablename__ = "audit_logs"

	id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
	user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
	action: Mapped[str] = mapped_column(String(100))
	details: Mapped[Optional[dict]] = mapped_column(JSON, default={})
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

	user: Mapped[Optional[User]] = relationship("User", back_populates="audit_logs")
