from pathlib import Path
import asyncio
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import pandas as pd

from app.core.config import settings
from app.db.session import get_db_session
from app.models.models import ImportBatch
from app.services.batch_processor import process_questions_file
from app.services.ingest import process_knowledge_a_file, process_standards_b_file

router = APIRouter(prefix="/imports", tags=["imports"])


class ImportResponse(BaseModel):
	ok: bool
	batch_id: int | None = None
	message: str = ""


class ImportBatchItem(BaseModel):
	id: int
	type: str
	status: str
	file_path: str
	metadata: dict | None = None
	created_at: str | None = None


@router.get("/batches", response_model=list[ImportBatchItem])
async def list_batches(db: AsyncSession = Depends(get_db_session)) -> list[ImportBatchItem]:
	res = await db.execute(select(ImportBatch).order_by(ImportBatch.id.desc()))
	items = []
	for b in res.scalars().all():
		items.append(ImportBatchItem(
			id=b.id, type=b.type, status=b.status, file_path=b.file_path, metadata=b.metadata, created_at=b.created_at.isoformat() if getattr(b, 'created_at', None) else None
		))
	return items


async def _save_upload(prefix: str, file: UploadFile) -> str:
	storage_dir = Path(settings.storage_base_dir) / "uploads" / prefix
	storage_dir.mkdir(parents=True, exist_ok=True)
	file_id = f"{uuid4().hex}_{file.filename}"
	path = storage_dir / file_id
	content = await file.read()
	path.write_bytes(content)
	return str(path)


def _validate_headers(file_path: str, required: list[str]) -> None:
	try:
		if file_path.lower().endswith((".xlsx", ".xls")):
			df = pd.read_excel(file_path, nrows=0)
		else:
			df = pd.read_csv(file_path, nrows=0, encoding_errors="ignore")
	except Exception:
		raise HTTPException(status_code=400, detail="无法读取文件，请确认为有效的 CSV/Excel")
	cols = set(df.columns.tolist())
	missing = [c for c in required if c not in cols]
	if missing:
		raise HTTPException(status_code=400, detail=f"缺少必要列: {', '.join(missing)}")


@router.post("/knowledge-a")
async def import_knowledge_a(
	file: UploadFile = File(...),
	kb_a_id: str = Query(...),
	db: AsyncSession = Depends(get_db_session),
) -> ImportResponse:
	path = await _save_upload("knowledge_a", file)
	_validate_headers(path, required=["title", "category", "source_path", "source_url", "disclosure_date"])  # allow empty values
	batch = ImportBatch(type="knowledge_a", file_path=path)
	db.add(batch)
	await db.commit()
	await db.refresh(batch)
	asyncio.create_task(process_knowledge_a_file(file_path=path, kb_a_id=kb_a_id, batch_id=batch.id))
	return ImportResponse(ok=True, batch_id=batch.id, message="processing started")


@router.post("/knowledge-a-hybrid")
async def import_knowledge_a_hybrid(
	csv_file: UploadFile = File(...),
	zip_file: UploadFile = File(...),
	kb_a_id: str = Query(...),
	db: AsyncSession = Depends(get_db_session),
) -> ImportResponse:
	"""混合模式：CSV提供元数据，ZIP包含PDF/DOCX文件，通过filename列匹配"""
	csv_path = await _save_upload("knowledge_a", csv_file)
	zip_path = await _save_upload("knowledge_a", zip_file)
	_validate_headers(csv_path, required=["title", "category", "filename"])  # filename用于匹配ZIP内文件
	batch = ImportBatch(type="knowledge_a_hybrid", file_path=csv_path, metadata={"zip_path": zip_path})
	db.add(batch)
	await db.commit()
	await db.refresh(batch)
	# 导入ingest的混合处理函数
	from app.services.ingest import process_knowledge_a_hybrid
	asyncio.create_task(process_knowledge_a_hybrid(csv_path=csv_path, zip_path=zip_path, kb_a_id=kb_a_id, batch_id=batch.id))
	return ImportResponse(ok=True, batch_id=batch.id, message="processing started (hybrid mode)")


@router.post("/knowledge-a-zip")
async def import_knowledge_a_zip(
	zip_file: UploadFile = File(...),
	kb_a_id: str = Query(...),
	default_category: str = Query("announcement"),
	db: AsyncSession = Depends(get_db_session),
) -> ImportResponse:
	"""纯ZIP模式：自动从文件名提取标题，批量上传PDF/DOCX到RAGFlow A"""
	zip_path = await _save_upload("knowledge_a", zip_file)
	batch = ImportBatch(type="knowledge_a_zip", file_path=zip_path, metadata={"default_category": default_category})
	db.add(batch)
	await db.commit()
	await db.refresh(batch)
	from app.services.ingest import process_knowledge_a_zip
	asyncio.create_task(process_knowledge_a_zip(zip_path=zip_path, kb_a_id=kb_a_id, default_category=default_category, batch_id=batch.id))
	return ImportResponse(ok=True, batch_id=batch.id, message="processing started (zip-only mode)")


@router.post("/standards-b")
async def import_standards_b(file: UploadFile = File(...), db: AsyncSession = Depends(get_db_session)) -> ImportResponse:
	path = await _save_upload("standards_b", file)
	_validate_headers(path, required=["topic_key", "content"])  # optional: strong_constraint, effective_from, effective_to, description
	batch = ImportBatch(type="standards_b", file_path=path)
	db.add(batch)
	await db.commit()
	await db.refresh(batch)
	asyncio.create_task(process_standards_b_file(file_path=path, batch_id=batch.id))
	return ImportResponse(ok=True, batch_id=batch.id, message="processing started")


@router.post("/questions")
async def import_questions(
	file: UploadFile = File(...),
	kb_a_id: str = Query(...),
	kb_b_id: str = Query(...),
	generate: bool = Query(True),
	prompt: str = Query(""),
	db: AsyncSession = Depends(get_db_session),
) -> ImportResponse:
	path = await _save_upload("questions", file)
	_validate_headers(path, required=["question"])
	batch = ImportBatch(type="questions", file_path=path)
	db.add(batch)
	await db.commit()
	await db.refresh(batch)
	asyncio.create_task(process_questions_file(file_path=path, kb_a_id=kb_a_id, kb_b_id=kb_b_id, prompt=prompt, generate=generate))
	return ImportResponse(ok=True, batch_id=batch.id, message="processing started")
