from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["audit"]) 


class AuditItem(BaseModel):
	id: int
	user_email: Optional[str]
	action: str
	details: dict | None
	created_at: str


@router.get("", response_model=List[AuditItem])
async def list_audit(db: AsyncSession = Depends(get_db_session), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> List[AuditItem]:
	res = await db.execute(select(AuditLog).order_by(AuditLog.id.desc()).offset(offset).limit(limit))
	items: List[AuditItem] = []
	for l in res.scalars().all():
		user_email = None
		# optional join: load user lazily
		items.append(AuditItem(
			id=l.id,
			user_email=user_email,
			action=l.action,
			details=l.details,
			created_at=l.created_at.isoformat() if l.created_at else ""
		))
	return items
