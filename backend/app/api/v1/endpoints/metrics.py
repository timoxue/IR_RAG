from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.models import Question, GeneratedAnswer, ReviewTask, StandardAnswerVersion, KnowledgeDoc

router = APIRouter(prefix="/metrics", tags=["metrics"]) 


@router.get("")
async def get_metrics(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
	counts = {}
	for model, key in [
		(Question, "questions"),
		(GeneratedAnswer, "generated_answers"),
		(ReviewTask, "review_tasks"),
		(StandardAnswerVersion, "standard_answer_versions"),
		(KnowledgeDoc, "knowledge_docs"),
	]:
		res = await db.execute(select(func.count()).select_from(model))
		counts[key] = int(res.scalar_one())
	return counts
