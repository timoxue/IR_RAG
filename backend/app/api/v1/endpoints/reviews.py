from typing import List, Optional, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.session import get_db_session
from app.models.models import ReviewTask, GeneratedAnswer, Question
from app.models.enums import ReviewStatus

router = APIRouter(prefix="/reviews", tags=["reviews"])


class ReviewTaskItem(BaseModel):
	id: int
	question_id: int
	status: str
	created_at: str


class ReviewTaskListResponse(BaseModel):
	tasks: List[ReviewTaskItem]


class ReviewDetail(BaseModel):
	id: int
	question_id: int
	status: str
	initial_answer: Optional[str]
	aligned_answer: Optional[str]
	alignment: Any
	evidence_a: Optional[dict]
	evidence_b: Optional[dict]


class ReviewActionRequest(BaseModel):
	comments: Optional[str] = None


class ReviewActionResponse(BaseModel):
	ok: bool
	status: str


@router.get("", response_model=ReviewTaskListResponse)
async def list_reviews(db: AsyncSession = Depends(get_db_session), status: Optional[str] = Query(None)) -> ReviewTaskListResponse:
	stmt = select(ReviewTask)
	if status:
		stmt = stmt.where(ReviewTask.status == status)
	res = await db.execute(stmt.order_by(ReviewTask.created_at.desc()))
	tasks = [
		ReviewTaskItem(
			id=t.id,
			question_id=t.question_id,
			status=t.status,
			created_at=t.created_at.isoformat() if t.created_at else "",
		)
		for t in res.scalars().all()
	]
	return ReviewTaskListResponse(tasks=tasks)


@router.get("/{task_id}", response_model=ReviewDetail)
async def get_review(task_id: int, db: AsyncSession = Depends(get_db_session)) -> ReviewDetail:
	res = await db.execute(select(ReviewTask).where(ReviewTask.id == task_id))
	task = res.scalar_one()
	res2 = await db.execute(select(GeneratedAnswer).where(GeneratedAnswer.id == task.generated_answer_id))
	ga = res2.scalar_one()
	alignment: Any
	try:
		alignment = json.loads(ga.alignment_summary or "{}")
	except Exception:
		alignment = {"raw": ga.alignment_summary}
	return ReviewDetail(
		id=task.id,
		question_id=task.question_id,
		status=task.status,
		initial_answer=ga.initial_answer,
		aligned_answer=ga.aligned_answer,
		alignment=alignment,
		evidence_a=ga.sources_a,
		evidence_b=ga.sources_b,
	)


@router.post("/{task_id}/approve", response_model=ReviewActionResponse)
async def approve(task_id: int, body: ReviewActionRequest, db: AsyncSession = Depends(get_db_session)) -> ReviewActionResponse:
	res = await db.execute(select(ReviewTask).where(ReviewTask.id == task_id))
	task = res.scalar_one()
	task.status = ReviewStatus.APPROVED.value
	task.comments = body.comments
	resq = await db.execute(select(Question).where(Question.id == task.question_id))
	q = resq.scalar_one()
	q.status = "answered"
	await db.commit()
	return ReviewActionResponse(ok=True, status=task.status)


@router.post("/{task_id}/request_changes", response_model=ReviewActionResponse)
async def request_changes(task_id: int, body: ReviewActionRequest, db: AsyncSession = Depends(get_db_session)) -> ReviewActionResponse:
	res = await db.execute(select(ReviewTask).where(ReviewTask.id == task_id))
	task = res.scalar_one()
	task.status = ReviewStatus.NEEDS_REVISION.value
	task.comments = body.comments
	await db.commit()
	return ReviewActionResponse(ok=True, status=task.status)


@router.post("/{task_id}/reject", response_model=ReviewActionResponse)
async def reject(task_id: int, body: ReviewActionRequest, db: AsyncSession = Depends(get_db_session)) -> ReviewActionResponse:
	res = await db.execute(select(ReviewTask).where(ReviewTask.id == task_id))
	task = res.scalar_one()
	task.status = ReviewStatus.REJECTED.value
	task.comments = body.comments
	await db.commit()
	return ReviewActionResponse(ok=True, status=task.status)
