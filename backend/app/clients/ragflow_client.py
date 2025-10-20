from typing import Any, Dict, List, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class RAGFlowClient:
	def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
		self.base_url = base_url or settings.ragflow_base_url
		self.api_key = api_key or settings.ragflow_api_key
		self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers)

	@property
	def _headers(self) -> Dict[str, str]:
		headers = {"Accept": "application/json"}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"
		return headers

	@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3))
	async def upload_document(self, file_path: str, kb_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		# Placeholder: adapt to RAGFlow v0.21.0 upload API
		files = {"file": open(file_path, "rb")}
		data = {"kb_id": kb_id}
		if metadata:
			data.update({f"meta_{k}": v for k, v in metadata.items()})
		resp = await self._client.post("/api/kb/upload", files=files, data=data)
		resp.raise_for_status()
		return resp.json()

	def _normalize_chunks(self, data: Dict[str, Any]) -> Dict[str, Any]:
		# Try common shapes: {'results': [...]} or {'chunks': [...]} or raw list
		raw = data.get("results") or data.get("chunks") or data.get("data") or data
		if isinstance(raw, dict) and "items" in raw:
			raw = raw.get("items")
		chunks: List[Dict[str, Any]] = []
		if isinstance(raw, list):
			for item in raw:
				text = item.get("text") or item.get("content") or item.get("chunk") or str(item)
				score = item.get("score") or item.get("similarity") or item.get("relevance") or 0
				meta = item.get("metadata") or item.get("meta") or {}
				chunks.append({"text": text, "score": float(score) if score is not None else 0.0, "metadata": meta})
		return {"chunks": chunks}

	@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3))
	async def query(self, kb_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
		payload = {"kb_id": kb_id, "query": query, "top_k": top_k}
		resp = await self._client.post("/api/kb/query", json=payload)
		resp.raise_for_status()
		data = resp.json()
		return self._normalize_chunks(data)

	async def aclose(self) -> None:
		await self._client.aclose()
