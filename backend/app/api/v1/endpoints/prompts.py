from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models.models import PromptTemplate
from app.api.deps import get_current_user, write_audit

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptIn(BaseModel):
	name: str
	content: str
	is_active: bool = True


class PromptOut(BaseModel):
	id: int
	name: str
	version: int
	content: str
	is_active: bool


@router.get("", response_model=List[PromptOut])
async def list_prompts(db: AsyncSession = Depends(get_db_session)) -> List[PromptOut]:
	res = await db.execute(select(PromptTemplate).order_by(PromptTemplate.name.asc(), PromptTemplate.version.desc()))
	items = res.scalars().all()
	return [PromptOut(id=i.id, name=i.name, version=i.version, content=i.content, is_active=i.is_active) for i in items]


@router.post("", response_model=PromptOut)
async def create_prompt(body: PromptIn, db: AsyncSession = Depends(get_db_session), user=Depends(get_current_user)) -> PromptOut:
	# new prompt starts at version 1
	pt = PromptTemplate(name=body.name, content=body.content, is_active=body.is_active, version=1)
	db.add(pt)
	await db.commit()
	await db.refresh(pt)
	await write_audit(db, user, action="prompt.create", details={"id": pt.id, "name": pt.name})
	return PromptOut(id=pt.id, name=pt.name, version=pt.version, content=pt.content, is_active=pt.is_active)


@router.post("/{name}/new_version", response_model=PromptOut)
async def new_prompt_version(name: str, body: PromptIn, db: AsyncSession = Depends(get_db_session), user=Depends(get_current_user)) -> PromptOut:
	res = await db.execute(select(PromptTemplate).where(PromptTemplate.name == name).order_by(PromptTemplate.version.desc()))
	latest = res.scalars().first()
	version = (latest.version + 1) if latest else 1
	pt = PromptTemplate(name=name, content=body.content, is_active=body.is_active, version=version)
	db.add(pt)
	await db.commit()
	await db.refresh(pt)
	await write_audit(db, user, action="prompt.new_version", details={"id": pt.id, "name": pt.name, "version": pt.version})
	return PromptOut(id=pt.id, name=pt.name, version=pt.version, content=pt.content, is_active=pt.is_active)


@router.patch("/{prompt_id}", response_model=PromptOut)
async def update_prompt(prompt_id: int, body: PromptIn, db: AsyncSession = Depends(get_db_session), user=Depends(get_current_user)) -> PromptOut:
	res = await db.execute(select(PromptTemplate).where(PromptTemplate.id == prompt_id))
	pt = res.scalar_one_or_none()
	if not pt:
		raise HTTPException(status_code=404, detail="prompt not found")
	pt.content = body.content
	pt.is_active = body.is_active
	await db.commit()
	await db.refresh(pt)
	await write_audit(db, user, action="prompt.update", details={"id": pt.id})
	return PromptOut(id=pt.id, name=pt.name, version=pt.version, content=pt.content, is_active=pt.is_active)
