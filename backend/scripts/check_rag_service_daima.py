import asyncio
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.schemas import RetrievalFilters
from app.services.rag_service import answer_question


async def main() -> None:
    question = "毕业论文查重比例超过多少要延期答辩"
    filters = RetrievalFilters()

    with SessionLocal() as session:
        result = await answer_question(
            session=session,
            question=question,
            filters=filters,
            mode="full",
            top_k=6,
            rerank_top_k=3,
            min_score=0.2,
        )

    print("问题：", question)
    print("是否拒答：", result.refused)
    print("耗时毫秒：", result.latency_ms)
    print("Token 使用：", result.token_usage)
    print("引用数量：", len(result.citations))
    print("回答：")
    print(result.answer)
    print()
    print("引用：")
    for citation in result.citations:
        print(
            {
                "label": citation["label"],
                "filename": citation["filename"],
                "section": citation["section"],
                "score": round(float(citation["score"]), 4),
                "quote_preview": citation["quote"][:80],
            }
        )
    print()
    print("检索调试：")
    print(
        {
            "rewritten_query": result.trace.get("rewritten_query"),
            "evidence_count": len(result.trace.get("final_evidence", [])),
            "citation_validation": result.trace.get("citation_validation"),
        }
    )


if __name__ == "__main__":
    asyncio.run(main())