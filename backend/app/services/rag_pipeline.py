from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import asyncio

from app.clients.ragflow_client import RAGFlowClient
from app.clients.deepseek_client import DeepSeekClient
from app.core.config import settings


class RAGPipeline:
	def __init__(self, rag_client: Optional[RAGFlowClient] = None, llm_client: Optional[DeepSeekClient] = None) -> None:
		self.rag_client = rag_client or RAGFlowClient()
		self.llm = llm_client or DeepSeekClient()

	async def retrieve_a_b(self, question: str, kb_a_id: str, kb_b_id: str, top_k_a: int = 5, top_k_b: int = 5) -> Tuple[Dict[str, Any], Dict[str, Any]]:
		res_a_task = asyncio.create_task(self.rag_client.query(kb_id=kb_a_id, query=question, top_k=top_k_a))
		res_b_task = asyncio.create_task(self.rag_client.query(kb_id=kb_b_id, query=question, top_k=top_k_b))
		res_a, res_b = await asyncio.gather(res_a_task, res_b_task)
		return res_a, res_b

	async def generate_initial_from_a(self, question: str, retrieved_a: Dict[str, Any], prompt: str) -> str:
		context = "\n\n".join([c.get("text", "") for c in retrieved_a.get("chunks", [])])
		composed_prompt = f"You are an IR assistant.\nQuestion: {question}\nContext (A):\n{context}\nInstructions:\n{prompt}"
		resp = await self.llm.chat(prompt=composed_prompt, model=settings.deepseek_model, temperature=settings.deepseek_temperature)
		answer = resp.get("choices", [{}])[0].get("message", {}).get("content", "") or str(resp)
		return answer

	def _extract_conflicts(self, mode: str, draft: str, b_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
		conflicts: List[Dict[str, Any]] = []
		if mode == "strong":
			# Example rule: ensure disclaimer exists
			if "免责声明" not in draft:
				conflicts.append({"type": "missing_disclaimer", "message": "缺少免责声明段落"})
		return conflicts

	async def align_with_b(self, draft: str, retrieved_b: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
		strong = settings.alignment_strong_threshold
		weak = settings.alignment_weak_threshold
		chunks = retrieved_b.get("chunks", [])
		scores: List[float] = [float(c.get("score", 0)) for c in chunks]
		max_score = max(scores) if scores else 0.0
		mode = "none"
		if max_score >= strong:
			mode = "strong"
		elif max_score >= weak:
			mode = "weak"
		else:
			mode = "free"
		conflicts = self._extract_conflicts(mode, draft, chunks)
		return draft, {"mode": mode, "max_score": max_score, "strong": strong, "weak": weak, "conflicts": conflicts}

	async def answer(self, question: str, prompt: str, kb_a_id: str, kb_b_id: str, top_k_a: int = 5, top_k_b: int = 5) -> Dict[str, Any]:
		retrieved_a, retrieved_b = await self.retrieve_a_b(question, kb_a_id, kb_b_id, top_k_a, top_k_b)
		initial = await self.generate_initial_from_a(question, retrieved_a, prompt)
		aligned, align_summary = await self.align_with_b(initial, retrieved_b)
		return {
			"initial": initial,
			"aligned": aligned,
			"evidence_a": retrieved_a,
			"evidence_b": retrieved_b,
			"alignment": align_summary,
		}
