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
		"""
		Upload document to RAGFlow dataset
		RAGFlow v0.21.0 API: POST /api/v1/datasets/{dataset_id}/documents
		"""
		# 使用正确的 API v1 端点
		with open(file_path, "rb") as f:
			files = {"file": f}
			# 根据 RAGFlow API 文档，使用 multipart/form-data
			resp = await self._client.post(
				f"/api/v1/datasets/{kb_id}/documents",
				files=files
			)
		resp.raise_for_status()
		result = resp.json()
		
		# 上传成功后，自动触发解析
		# RAGFlow API 返回格式: {"code": 0, "data": {"id": "...", ...}}
		if isinstance(result, dict):
			code = result.get("code")
			data = result.get("data")
			
			if code == 0 and data:
				# data 可能是字典或列表
				if isinstance(data, dict):
					doc_id = data.get("id")
				elif isinstance(data, list) and len(data) > 0:
					doc_id = data[0].get("id") if isinstance(data[0], dict) else None
				else:
					doc_id = None
				
				if doc_id:
					try:
						await self.parse_document(kb_id, doc_id)
					except Exception as e:
						# 解析失败不影响上传结果，记录日志
						import logging
						logging.warning(f"Failed to trigger parse for doc {doc_id}: {e}")
		
		return result
	
	@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3))
	async def parse_document(self, kb_id: str, doc_id: str) -> Dict[str, Any]:
		"""
		Trigger document parsing
		RAGFlow v0.21.0 API: POST /api/v1/datasets/{dataset_id}/chunks
		"""
		payload = {"document_ids": [doc_id]}
		resp = await self._client.post(
			f"/api/v1/datasets/{kb_id}/chunks",
			json=payload
		)
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
