from typing import Optional
from fastapi import Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.models import User, AuditLog


async def get_current_user(x_user_email: Optional[str] = Header(default=None), db: AsyncSession = Depends(get_db_session)) -> Optional[User]:
	if not x_user_email:
		return None
	res = await db.execute(select(User).where(User.email == x_user_email))
	user = res.scalar_one_or_none()
	if not user:
		user = User(email=x_user_email, name=x_user_email.split('@')[0] if '@' in x_user_email else x_user_email)
		db.add(user)
		await db.commit()
		await db.refresh(user)
	return user


async def write_audit(db: AsyncSession, user: Optional[User], action: str, details: Optional[dict] = None) -> None:
	log = AuditLog(user_id=user.id if user else None, action=action, details=details or {})
	db.add(log)
	await db.commit()
