from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
	env: str = "dev"
	mysql_user: str = "root"
	mysql_password: str = "password"
	mysql_host: str = "localhost"
	mysql_port: int = 3306
	mysql_db: str = "ir_rag"

	ragflow_base_url: str = "http://localhost:7860"
	ragflow_api_key: str = ""
	deepseek_api_key: str = ""
	qwen_api_key: str = ""
	llm_provider: str = "qwen"  # qwen, deepseek, openai
	llm_model: str = "qwen-max"  # qwen-max, deepseek-chat, gpt-4, etc.
	deepseek_model: str = "deepseek-chat"
	deepseek_temperature: float = 0.2

	alignment_strong_threshold: float = 0.8
	alignment_weak_threshold: float = 0.6

	storage_base_dir: str = "./storage"
	cors_allow_origins: List[str] = ["*"]

	@property
	def database_url(self) -> str:
		return (
			f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
			f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
		)

	model_config = {
		"env_file": ".env",
		"env_file_encoding": "utf-8",
	}


settings = Settings()
