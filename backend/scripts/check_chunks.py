import sys
from pathlib import Path

from sqlalchemy import func, select


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import Base, SessionLocal
from app.models import DocumentChunk, PolicyDocument


def main() -> None:
    from app import models  # noqa: F401

    print("ORM 注册表：")
    print(Base.metadata.tables.keys())

    with SessionLocal() as session:
        document_count = session.scalar(select(func.count(PolicyDocument.id)))
        chunk_count = session.scalar(select(func.count(DocumentChunk.id)))
        parent_count = session.scalar(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.is_parent.is_(True))
        )
        child_count = session.scalar(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.is_parent.is_(False))
        )

        print("文档数量：", document_count)
        print("分块总数：", chunk_count)
        print("父块数量：", parent_count)
        print("子块数量：", child_count)

        rows = list(
            session.scalars(
                select(DocumentChunk).order_by(DocumentChunk.ordinal).limit(5)
            ).all()
        )
        print("前 5 个分块：")
        for row in rows:
            print(
                {
                    "id": row.id,
                    "document_id": row.document_id,
                    "parent_id": row.parent_id,
                    "ordinal": row.ordinal,
                    "section": row.section,
                    "page": row.page,
                    "is_parent": row.is_parent,
                    "token_count": row.token_count,
                    "content_preview": row.content[:40],
                }
            )


if __name__ == "__main__":
    main()