import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.sql.expression import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import Base, SessionLocal
from app.models import PolicyDocument, DocumentStatus
from app.schemas import DocumentOut

def check_metadata() -> None:
    from app import models

    print("ORM 注册表：")
    print(Base.metadata.tables.keys())

# 直接连接数据库，查询 policy_documents 表全部数据，打印核心字段，快速查看数据库内文档状态
def check_database_rows() -> None:
    with SessionLocal() as session:
        rows = list(session.scalars(select(PolicyDocument)).all())
        print("文档记录：")
        print(
            [
                (row.filename, row.topic, row.status.value, row.chunk_count)
                for row in rows
            ]
        )

def check_schema() -> None:
    # 手动构造一个SQLAlchemy ORM模型实例（模拟数据库查询出来的PolicyDocument对象）
    document = PolicyDocument(
        id="demo-document-id",
        filename="a.txt",
        stored_path="data/uploads/a.txt",
        content_type="text/plain",
        topic="人才政策",
        effective_date=None,
        status=DocumentStatus.ready,
        chunk_count=0,
        index_version=1,
        created_at=datetime.now(),
    )
    # ORM对象 → Pydantic模型转换
    output = DocumentOut.model_validate(document)
    print("Schema 转换结果：")
    print(output)

# 作用：打印当前应用中所有以 /api 开头的接口路径，用来验证路由是否成功注册到 FastAPI 实例。
def check_routes() -> None:
    import main

    routes = [route.path for route in main.app.routes if route.path.startswith("/api")]
    print("API 路由：")
    print(routes)

if __name__ == '__main__':
    check_schema()
    check_metadata()
    check_database_rows()
    check_routes()

#
#     # DocumentOut 能否从 ORM 对象转换。
#  /api/documents 路由是否注册。
#  MySQL 中当前有哪些文档记录。