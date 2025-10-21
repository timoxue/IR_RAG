from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class LLMClient:
	"""通用 LLM 客户端，支持 Qwen、DeepSeek、OpenAI 等"""
	
	def __init__(self, provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
		self.provider = provider or settings.llm_provider
		self.model = model or settings.llm_model
		
		# 根据提供商选择对应的 API Key
		if api_key:
			self.api_key = api_key
		elif self.provider == "qwen":
			self.api_key = settings.qwen_api_key
		elif self.provider == "deepseek":
			self.api_key = settings.deepseek_api_key
		else:
			self.api_key = settings.deepseek_api_key  # 默认
		
		# 根据提供商设置 base_url
		if self.provider == "qwen":
			self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
		elif self.provider == "deepseek":
			self.base_url = "https://api.deepseek.com"
		elif self.provider == "openai":
			self.base_url = "https://api.openai.com/v1"
		else:
			self.base_url = "https://api.deepseek.com"  # 默认
		
		self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=60.0)

	@property
	def _headers(self) -> Dict[str, str]:
		headers = {"Accept": "application/json", "Content-Type": "application/json"}
		if self.api_key:
			if self.provider == "qwen":
				headers["Authorization"] = f"Bearer {self.api_key}"
			else:
				headers["Authorization"] = f"Bearer {self.api_key}"
		return headers

	@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3))
	async def chat(self, prompt: str, model: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
		"""统一的 chat completion 接口"""
		use_model = model or self.model
		
		# 标准 OpenAI 格式（Qwen、DeepSeek 都兼容）
		payload = {
			"model": use_model,
			"messages": [{"role": "user", "content": prompt}],
			"temperature": temperature
		}
		
		resp = await self._client.post("/chat/completions", json=payload)
		resp.raise_for_status()
		return resp.json()

	async def aclose(self) -> None:
		await self._client.aclose()


# 保持向后兼容
class DeepSeekClient(LLMClient):
	"""DeepSeek 客户端（向后兼容）"""
	def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
		super().__init__(provider="deepseek", api_key=api_key)
		if base_url:
			self.base_url = base_url
			self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=60.0)

