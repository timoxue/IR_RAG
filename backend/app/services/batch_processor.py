from __future__ import annotations
from typing import Optional, List
import asyncio
import pandas as pd

from app.db.session import AsyncSessionLocal
from app.models.models import Question, GeneratedAnswer, ReviewTask
from app.services.rag_pipeline import RAGPipeline


async def _generate_and_store(question: Question, kb_a_id: str, kb_b_id: str, prompt: str) -> None:
	pipeline = RAGPipeline()
	result = await pipeline.answer(question=question.asked_text, prompt=prompt or "", kb_a_id=kb_a_id, kb_b_id=kb_b_id)
	async with AsyncSessionLocal() as db:
		ga = GeneratedAnswer(
			question_id=question.id,
			initial_answer=result["initial"],
			aligned_answer=result["aligned"],
			alignment_summary=str(result.get("alignment", {})),
			sources_a=result.get("evidence_a"),
			sources_b=result.get("evidence_b"),
		)
		db.add(ga)
		await db.flush()
		review = ReviewTask(question_id=question.id, generated_answer_id=ga.id)
		db.add(review)
		question.status = "answered"
		await db.commit()


async def process_questions_file(file_path: str, kb_a_id: str, kb_b_id: str, prompt: str = "", generate: bool = True) -> int:
	"""Parse CSV/Excel file with a column named 'question' and create Question rows.
	If generate=True, run pipeline per question and create GeneratedAnswer & ReviewTask.
	Returns the number of questions processed.
	"""
	# Read file via pandas
	if file_path.lower().endswith((".xlsx", ".xls")):
		df = pd.read_excel(file_path)
	else:
		df = pd.read_csv(file_path, encoding_errors="ignore")
	if "question" not in df.columns:
		raise ValueError("questions file must contain a 'question' column")

	texts: List[str] = [str(x) for x in df["question"].dropna().tolist()]
	count = 0
	async with AsyncSessionLocal() as db:
		for qtext in texts:
			q = Question(asked_text=qtext, status="pending")
			db.add(q)
			await db.flush()
			count += 1
			if generate:
				asyncio.create_task(_generate_and_store(q, kb_a_id=kb_a_id, kb_b_id=kb_b_id, prompt=prompt))
		await db.commit()
	return count
