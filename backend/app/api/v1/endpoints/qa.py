from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.rag_pipeline import RAGPipeline


class QARequest(BaseModel):
	question: str
	prompt: str = ""
	kb_a_id: str
	kb_b_id: str
	top_k_a: int = 5
	top_k_b: int = 5


class QAResponse(BaseModel):
	initial: str
	aligned: str
	evidence_a: dict
	evidence_b: dict
	alignment: dict


router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/answer", response_model=QAResponse)
async def answer(req: QARequest) -> QAResponse:
	pipeline = RAGPipeline()
	result = await pipeline.answer(
		question=req.question,
		prompt=req.prompt,
		kb_a_id=req.kb_a_id,
		kb_b_id=req.kb_b_id,
		top_k_a=req.top_k_a,
		top_k_b=req.top_k_b,
	)
	return QAResponse(**result)
