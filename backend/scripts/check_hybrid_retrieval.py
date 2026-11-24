import asyncio
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.schemas import RetrievalFilters
from app.services.retrieval import retrieve


def print_items(title: str, rows: list[dict], limit: int = 5) -> None:
    print(title)
    for item in rows[:limit]:
        metadata = item.get("metadata", {})
        print(
            {
                "chunk_id": item.get("chunk_id"),
                "source": item.get("source"),
                "score": round(float(item.get("score", 0)), 4),
                "rrf_score": round(float(item.get("rrf_score", 0)), 4),
                "sources": item.get("sources"),
                "filename": metadata.get("filename"),
                "section": metadata.get("section"),
                "content_preview": item.get("content", "")[:60],
            }
        )


async def main() -> None:
    question = "国家奖学金8000元"
    filters = RetrievalFilters()

    with SessionLocal() as session:
        result = await retrieve(
            session=session,
            question=question,
            filters=filters,
            #mode="hybrid",   先注释掉
            top_k=5,
            evidence_top_k=3,  # 换成这个  evidence_top_k=3  测试
            min_score=0.1,
        )

    trace = result.trace
    print("问题：", question)
    print("是否拒答：", result.refused)
    print("候选数量：", len(result.candidates))
    print("证据数量：", len(result.evidence))
    print()

    print_items("向量检索结果：", trace.get("vector_results", []))
    print()
    print_items("BM25 检索结果：", trace.get("keyword_results", []))
    print()
    print_items("RRF 融合结果：", trace.get("fused_results", []))
    print()
    print_items("最终证据：", result.evidence)


if __name__ == "__main__":
    asyncio.run(main())