# BM25检索输出，每一项必须有chunk_id、source字段
from app.services.pipeline_utils import reciprocal_rank_fusion

bm25_out = [
    {"chunk_id":"ch001", "content":"xxx1", "source":"bm25"},
    {"chunk_id":"ch002", "content":"xxx2", "source":"bm25"},
]
# 向量检索输出
vec_out = [
    {"chunk_id":"ch002", "content":"xxx2", "source":"vector"},
    {"chunk_id":"ch003", "content":"xxx3", "source":"vector"},
]

fused_all = reciprocal_rank_fusion([bm25_out, vec_out], k=60)

# 取top5
final_top5 = fused_all[:5]

# 输出示例单条 item：

{
    "chunk_id":"ch002",
    "content":"xxx2",
    "source":"bm25",
    "rrf_score": 0.032,
    "sources":["bm25","vector"]
}