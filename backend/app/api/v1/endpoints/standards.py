from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.models import StandardAnswer, StandardAnswerVersion


class PromoteRequest(BaseModel):
	topic_key: str
	content: str
	strong_constraint: bool = False
	effective_from: Optional[datetime] = None
	effective_to: Optional[datetime] = None
	description: Optional[str] = None


class PromoteResponse(BaseModel):
	ok: bool
	message: str = ""
	version: int | None = None


router = APIRouter(prefix="/standards", tags=["standards"])


@router.post("/promote", response_model=PromoteResponse)
async def promote_standard(req: PromoteRequest, db: AsyncSession = Depends(get_db_session)) -> PromoteResponse:
	# upsert standard_answers by topic_key
	result = await db.execute(select(StandardAnswer).where(StandardAnswer.topic_key == req.topic_key))
	sa = result.scalar_one_or_none()
	if not sa:
		sa = StandardAnswer(topic_key=req.topic_key, description=req.description)
		db.add(sa)
		await db.flush()

	# compute next version
	res_ver = await db.execute(
		select(func.coalesce(func.max(StandardAnswerVersion.version), 0)).where(StandardAnswerVersion.standard_answer_id == sa.id)
	)
	current_max = int(res_ver.scalar_one()) if res_ver.scalar() is not None else 0
	next_version = current_max + 1

	sav = StandardAnswerVersion(
		standard_answer_id=sa.id,
		version=next_version,
		content=req.content,
		strong_constraint=req.strong_constraint,
		effective_from=req.effective_from,
		effective_to=req.effective_to,
	)
	db.add(sav)
	await db.commit()
	return PromoteResponse(ok=True, message="Promoted to standard", version=next_version)
