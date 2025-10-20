from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db_session

router = APIRouter(prefix="/health")


@router.get("", summary="Health check")
async def health_check(db: AsyncSession = Depends(get_db_session)) -> dict:
	try:
		await db.execute(text("SELECT 1"))
		db_ok = True
	except Exception:
		db_ok = False
	return {"status": "ok", "db": db_ok}
