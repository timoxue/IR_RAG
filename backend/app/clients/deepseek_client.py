from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class DeepSeekClient:
	def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
		self.base_url = base_url or "https://api.deepseek.com"  # placeholder
		self.api_key = api_key or settings.deepseek_api_key
		self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers)

	@property
	def _headers(self) -> Dict[str, str]:
		headers = {"Accept": "application/json"}
		if self.api_key:
			headers["Authorization"] = f"Bearer {self.api_key}"
		return headers

	@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3))
	async def chat(self, prompt: str, model: str = "deepseek-chat", temperature: float = 0.2) -> Dict[str, Any]:
		# Placeholder schema; adapt to actual DeepSeek API
		payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature}
		resp = await self._client.post("/chat/completions", json=payload)
		resp.raise_for_status()
		return resp.json()

	async def aclose(self) -> None:
		await self._client.aclose()
