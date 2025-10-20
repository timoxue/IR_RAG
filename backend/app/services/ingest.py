from __future__ import annotations
from typing import Optional, List
from datetime import datetime
import pandas as pd
import sqlalchemy as sa

from app.db.session import AsyncSessionLocal
from app.models.models import KnowledgeDoc, ImportBatch, StandardAnswer, StandardAnswerVersion
from app.models.enums import DocCategory, ImportStatus
from app.clients.ragflow_client import RAGFlowClient


async def _update_batch(batch_id: int, status: str, message: Optional[str] = None) -> None:
	async with AsyncSessionLocal() as db:
		res = await db.execute(sa.select(ImportBatch).where(ImportBatch.id == batch_id))
		b = res.scalar_one_or_none()
		if b:
			b.status = status
			meta = dict(b.metadata or {})
			if message:
				meta["message"] = message
			b.metadata = meta
			await db.commit()


async def process_knowledge_a_file(file_path: str, kb_a_id: str, default_category: str = DocCategory.ANNOUNCEMENT.value, batch_id: Optional[int] = None) -> int:
	if batch_id is not None:
		await _update_batch(batch_id, ImportStatus.PROCESSING.value)
	try:
		if file_path.lower().endswith((".xlsx", ".xls")):
			df = pd.read_excel(file_path)
		else:
			df = pd.read_csv(file_path, encoding_errors="ignore")

		rows = df.to_dict(orient="records")
		count = 0
		rag = RAGFlowClient()
		async with AsyncSessionLocal() as db:
			for r in rows:
				title = str(r.get("title") or "").strip()
				if not title:
					continue
				category = str(r.get("category") or default_category)
				source_path = r.get("source_path")
				source_url = r.get("source_url")
				disclosure_date = r.get("disclosure_date")
				if disclosure_date:
					try:
						disclosure_date = datetime.fromisoformat(str(disclosure_date)).date()
					except Exception:
						disclosure_date = None
				kd = KnowledgeDoc(
					title=title,
					category=category,
					source_path=source_path,
					source_url=source_url,
					disclosure_date=disclosure_date,
				)
				db.add(kd)
				await db.flush()
				if source_path:
					try:
						await rag.upload_document(file_path=source_path, kb_id=kb_a_id, metadata={"doc_id": kd.id, "category": category})
					except Exception:
						pass
				count += 1
			await db.commit()
		if batch_id is not None:
			await _update_batch(batch_id, ImportStatus.COMPLETED.value, message=f"processed={count}")
		return count
	except Exception as e:
		if batch_id is not None:
			await _update_batch(batch_id, ImportStatus.FAILED.value, message=str(e))
		raise


async def process_standards_b_file(file_path: str, batch_id: Optional[int] = None) -> int:
	if batch_id is not None:
		await _update_batch(batch_id, ImportStatus.PROCESSING.value)
	try:
		if file_path.lower().endswith((".xlsx", ".xls")):
			df = pd.read_excel(file_path)
		else:
			df = pd.read_csv(file_path, encoding_errors="ignore")
		rows = df.to_dict(orient="records")
		count = 0
		async with AsyncSessionLocal() as db:
			for r in rows:
				topic_key = str(r.get("topic_key") or "").strip()
				content = str(r.get("content") or "").strip()
				if not topic_key or not content:
					continue
				strong = bool(r.get("strong_constraint") or False)
				desc = r.get("description")
				def _parse_dt(v):
					if not v:
						return None
					try:
						return datetime.fromisoformat(str(v))
					except Exception:
						return None
				eff_from = _parse_dt(r.get("effective_from"))
				eff_to = _parse_dt(r.get("effective_to"))

				res = await db.execute(sa.select(StandardAnswer).where(StandardAnswer.topic_key == topic_key))
				sa_obj = res.scalar_one_or_none()
				if not sa_obj:
					sa_obj = StandardAnswer(topic_key=topic_key, description=desc)
					db.add(sa_obj)
					await db.flush()
				res_ver = await db.execute(sa.select(sa.func.coalesce(sa.func.max(StandardAnswerVersion.version), 0)).where(StandardAnswerVersion.standard_answer_id == sa_obj.id))
				current_max = int(res_ver.scalar_one()) if res_ver.scalar() is not None else 0
				next_version = current_max + 1
				sav = StandardAnswerVersion(
					standard_answer_id=sa_obj.id,
					version=next_version,
					content=content,
					strong_constraint=strong,
					effective_from=eff_from,
					effective_to=eff_to,
				)
				db.add(sav)
				count += 1
			await db.commit()
		if batch_id is not None:
			await _update_batch(batch_id, ImportStatus.COMPLETED.value, message=f"processed={count}")
		return count
	except Exception as e:
		if batch_id is not None:
			await _update_batch(batch_id, ImportStatus.FAILED.value, message=str(e))
		raise
