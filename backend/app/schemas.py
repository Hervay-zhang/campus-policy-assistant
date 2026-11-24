from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
	model_config = ConfigDict(extra="forbid")

class ORMModel(APIModel):
	model_config = ConfigDict(from_attributes=True, extra="forbid")
	#以下是解读:
		#控制额外字段处理策略，一共三种可选：
			# extra="forbid"
			# ❌ 不允许传入模型未定义的字段
			# 请求 JSON 包含多余字段 → 直接抛出验证错误，返回 422。
			# extra="ignore"
			# 忽略多余未知字段，直接丢弃，不报错。
			# extra="allow"
			# 接收额外字段，并保存到模型实例中。
			#
			# model_config 是一种配置，不是一个字段！！！！
			#


# 将上传文件的结果封装到这个实体中，返回给界面使用的
# DocumentOut 是文档接口返回给前端的数据结构。
class DocumentOut(ORMModel):
	id: str
	filename: str
	content_type: str
	topic: str | None
	effective_date: date | None
	status: str
	error_message: str | None
	chunk_count: int
	index_version: int
	created_at: datetime
## 传递过滤条件的数据使用的

class RetrievalFilters(APIModel):
    document_ids: list[str] = Field(default_factory=list)
    topic: str | None = None
    effective_before: date | None = None

#定义了聊天请求模型
class ChatRequest(APIModel):
    question: str = Field(min_length=2, max_length=2000)
    conversation_id: str | None = None
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    debug: bool = False


#以下是ollama参数
from typing import Literal, Any


# 用于接受前端传递的参数
class ModelConfigIn(APIModel):
    provider: Literal["ollama", "deepseek"]
    model: str | None = None
    base_url: str | None = None

# 用于后台传递给前端的数据
class ModelConfigOut(APIModel):
    provider: str
    model: str
    base_url: str
    configured: bool

#单条测试用例输入：
class EvaluationCaseIn(APIModel):
    question: str
    reference_answer: str = ""
    expected_chunk_ids: list[str] = Field(default_factory=list)
    question_type: str = "direct"
    should_refuse: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

#创建测试集：
class DatasetCreate(APIModel):
    name: str
    description: str | None = None
    cases: list[EvaluationCaseIn] = Field(default_factory=list)

#创建评估任务
class RunCreate(APIModel):
    dataset_id: str
    name: str
    mode: Literal["vector", "hybrid", "hybrid_rerank", "full"] = "full"
    top_k: int = Field(default=8, ge=1, le=50)
    rerank_top_k: int = Field(default=4, ge=1, le=20)
    min_evidence_score: float = Field(default=0.25, ge=0, le=1)
    enable_judge: bool = False

#人工复核分数：
class ManualScoreIn(APIModel):
    faithfulness: float | None = Field(default=None, ge=0, le=1)
    relevance: float | None = Field(default=None, ge=0, le=1)
    factual_accuracy: float | None = Field(default=None, ge=0, le=1)
    notes: str = ""