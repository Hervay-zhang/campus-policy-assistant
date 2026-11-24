"""把 sample_data 里的高校教务政策文件导入知识库。

用法（在 backend 目录下，需先启动 ollama 并拉取嵌入模型）：
    ..\\.venv\\Scripts\\python.exe scripts/import_sample_data.py            # 清空后重新导入
    ..\\.venv\\Scripts\\python.exe scripts/import_sample_data.py --keep     # 保留已有文档，只追加

导入流程与页面上传完全一致：解析 → 父子分块 → 向量化写入 Milvus → 落库 MySQL。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete

from app.database import SessionLocal
from app.models import Citation, ChatMessage, Conversation, DocumentChunk, PolicyDocument
from app.services.document_service import ingest_upload
from app.services.vector_store import VectorStoreService

SAMPLES: list[tuple[str, str, date]] = [
    ("广东工业大学本科生学籍管理规定.docx", "学籍管理", date(2025, 9, 1)),
    ("广东工业大学本科生课程考核与成绩管理办法.txt", "课程考核", date(2025, 9, 1)),
    ("广东工业大学本科生转专业管理办法.txt", "转专业", date(2025, 3, 1)),
    ("广东工业大学国家奖学金与国家励志奖学金评审实施细则.txt", "奖助学金", date(2025, 9, 1)),
    ("广东工业大学本科毕业论文（设计）管理办法.pdf", "毕业论文", date(2025, 9, 1)),
    ("广东工业大学学士学位授予工作细则.txt", "学位授予", date(2025, 9, 1)),
]


async def reset_knowledge_base(session) -> None:
    """清空向量库与文档相关数据，避免旧政策残留。"""
    await VectorStoreService().reset()
    session.execute(delete(Citation))
    session.execute(delete(ChatMessage))
    session.execute(delete(Conversation))
    session.execute(delete(DocumentChunk))
    session.execute(delete(PolicyDocument))
    session.commit()
    print("已清空向量库与历史文档、会话数据")


async def main(keep: bool) -> None:
    sample_dir = BACKEND_ROOT / "sample_data"
    missing = [name for name, _, _ in SAMPLES if not (sample_dir / name).exists()]
    if missing:
        raise SystemExit(f"缺少示例文件：{missing}，请先运行 scripts/make_sample_docs.py")

    with SessionLocal() as session:
        if not keep:
            await reset_knowledge_base(session)

        for filename, topic, effective_date in SAMPLES:
            path = sample_dir / filename
            upload = _as_upload(path)
            document = await ingest_upload(session, upload, topic, effective_date)
            print(f"已导入 {document.filename}｜主题 {topic}｜分块 {document.chunk_count}")


def _as_upload(path: Path):
    from starlette.datastructures import UploadFile

    suffix = path.suffix.lower()
    content_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
    }[suffix]
    return UploadFile(filename=path.name, file=path.open("rb"), headers={"content-type": content_type})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入高校教务政策示例数据")
    parser.add_argument("--keep", action="store_true", help="保留已有文档，仅追加导入")
    args = parser.parse_args()
    asyncio.run(main(args.keep))
