import asyncio
import sys
from pathlib import Path

from pymilvus import Collection
from sqlalchemy import func, select


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.models import DocumentChunk, PolicyDocument
from app.services.vector_store import VectorStoreService, get_vector_store
from app.services.document_service import delete_document, rebuild_index


async def main() -> None:
    store = VectorStoreService()

    with SessionLocal() as session:
        child_count = session.scalar(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.is_parent.is_(False))
        )
        print("MySQL 子块数量：", child_count)

        rows = list(
            session.execute(
                select(DocumentChunk, PolicyDocument)
                .join(PolicyDocument, DocumentChunk.document_id == PolicyDocument.id)
                .where(DocumentChunk.is_parent.is_(False))
                .order_by(DocumentChunk.ordinal)
            ).all()
        )

        if not rows:
            print("当前没有子块，请先上传文档并完成分块入库。")
            return

        grouped: dict[str, tuple[PolicyDocument, list[DocumentChunk]]] = {}
        for chunk, document in rows:
            grouped.setdefault(document.id, (document, []))[1].append(chunk)

        for document, chunks in grouped.values():
            await store.add_chunks(document, chunks)

    vec = get_vector_store()
    print("Milvus 集合名称：", vec.collection_name)

    query = "国家奖学金申请需要满足哪些条件"
    results = await store.search(query, top_k=3)
    print("检索问题：", query)
    print("向量检索结果：")
    for item in results:
        print(
            {
                "chunk_id": item["chunk_id"],
                "score": round(item["score"], 4),
                "filename": item["metadata"].get("filename"),
                "section": item["metadata"].get("section"),
                "content_preview": item["content"][:60],
            }
        )


if __name__ == "__main__":
    # asyncio.run(main())
    # 测试删除文件包含数据库数据以及向量数据
    with SessionLocal() as session:
        # document=session.query(PolicyDocument).filter(PolicyDocument.id=="22e96a52-aa61-45bc-8767-acb29860983f").first()
        # asyncio.run(delete_document(session,document))
        nums = asyncio.run(rebuild_index(session))
        print(nums)