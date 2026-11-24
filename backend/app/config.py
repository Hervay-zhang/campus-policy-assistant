from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> parent=app, parent.parent=backend
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "校园百事通 · 高校教务政策 RAG 智能咨询系统"
    debug: bool = True
    api_prefix: str = "/api"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    database_url: str = "mysql+pymysql://root:123456@127.0.0.1:3306/edu_rag?charset=utf8mb4"

    upload_path: Path = BASE_DIR / "data/uploads"
    max_upload_mb: int = 20

    # # 以下是milvus的下向量储存
    milvus_path: Path = BASE_DIR / "data/milvus"
    embedding_model: str = "qwen3.7-text-embedding"
    dashscope_api_key: str = ""

    #第十二章
    reranker_model: str = "BAAI/bge-reranker-base"
    enable_vector_search: bool = True
    enable_reranker: bool = True
    rerank_top_k: int = 4
    min_evidence_score: float = 0.25

    model_config = SettingsConfigDict(
        env_file=("../.env",".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #ollama配置
    model_provider: Literal["ollama", "deepseek"] = "ollama"

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"

    @model_validator(mode="after")
    def _resolve_relative_paths(self):
        # .env 里写的仍然是相对路径(data/uploads 等)，统一解析成基于 backend 目录的绝对路径，
        # 这样无论从哪个工作目录启动服务都不会找不到数据文件
        for name in ("upload_path", "milvus_path"):
            value = getattr(self, name)
            if not value.is_absolute():
                object.__setattr__(self, name, (BASE_DIR / value).resolve())
        return self


@lru_cache()
def get_settings():
    return Settings()
