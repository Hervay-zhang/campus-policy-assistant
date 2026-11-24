import asyncio
import hashlib
from datetime import date, datetime
from pathlib import Path

from sqlalchemy.orm.session import Session
from fastapi import  UploadFile

from app.config import get_settings
from app.models import DocumentStatus, PolicyDocument, DocumentChunk
from app.schemas import DocumentOut
from app.services.chunking import split_policy_text
from app.services.vector_store import VectorStoreService

# set集合
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

async def save_upload(session: Session,
    upload: UploadFile,
    topic: str | None = None,
    effective_date: date | None = None,):
    fileName = upload.filename
    # 校验一下文件的后缀
    suffix = Path(fileName).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 PDF、DOCX、TXT 文件")
    # 校验一下文件的大小
    content = await upload.read()
    settings = get_settings()
    if len(content) > settings.max_upload_mb*1024*1024:
        raise ValueError("文件大小超出限制")
    #如果上传的文件夹不存在，则创建
    upload_path=settings.upload_path
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

    #将数据保存到数据库里
    document = PolicyDocument(
        filename=upload.filename or f"policy{suffix}",
        stored_path="",
        content_type=upload.content_type or "application/octet-stream",
        topic=topic,
        effective_date=effective_date,
        status=DocumentStatus.ready,
    )
    session.add(document)
    # 获取数据库uuid
    session.flush()

    # uploadPath 绝对不是一个字符串，而是一个Path 对象
    uploadPath = settings.upload_path / f"{document.id}{suffix}"
    uploadPath.write_bytes(content)

    document.stored_path = str(uploadPath)

    session.commit()

    print("上传成功")

    return document

# 将文件上传，并将文件信息和切块信息一起保存到数据库里
async def ingest_upload(session: Session,
    upload: UploadFile,
    topic: str | None = None,
    effective_date: date | None = None,):
    fileName = upload.filename
    # 校验一下文件的后缀
    suffix = Path(fileName).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("仅支持 PDF、DOCX、TXT 文件")
    # 校验一下文件的大小
    content = await upload.read()
    settings = get_settings()
    if len(content) > settings.max_upload_mb*1024*1024:
        raise ValueError("文件大小超出限制")

    # 内容指纹：同一份文件重复上传直接拦截，避免同一批条款被索引两遍
    md5 = hashlib.md5(content).hexdigest()
    duplicated = (
        session.query(PolicyDocument)
        .filter(PolicyDocument.md5 == md5)
        .first()
    )
    if duplicated:
        raise ValueError(f"该文件已入库（{duplicated.filename}），无需重复上传")

    # 同名文件但内容有更新时，先清掉旧分块与旧向量，再按新版本重新索引
    previous = (
        session.query(PolicyDocument)
        .filter(PolicyDocument.filename == fileName)
        .first()
    )
    if previous:
        await delete_document(session, previous)

    #如果上传的文件夹不存在，则创建
    upload_path=settings.upload_path
    if not upload_path.exists():
        upload_path.mkdir(parents=True, exist_ok=True)

    #将数据保存到数据库里
    document = PolicyDocument(
        filename=upload.filename or f"policy{suffix}",
        stored_path="",
        content_type=upload.content_type or "application/octet-stream",
        md5=md5,
        topic=topic,
        effective_date=effective_date,
        status=DocumentStatus.indexing,
    )
    session.add(document)
    # 获取数据库uuid
    session.flush()

    # uploadPath 绝对不是一个字符串，而是一个Path 对象
    uploadPath = settings.upload_path / f"{document.id}{suffix}"
    uploadPath.write_bytes(content)

    document.stored_path = str(uploadPath)

    #添加父子块信息
    # 存放所有的子块信息
    # #################################################
    chunk_rows: list[DocumentChunk] = []
    # vector_records: list[DocumentChunk] = []
    # if not uploadPath.is_parent:
    #     vector_records.append(chunk_rows)

    # 此处的page 是页码，text 是页内容
    ordinal = 0 # 从父块到子块的编号
    for page,text in extract_pages(uploadPath):
        # 将每一页的信息进行父子切块，父块和子块都在drafts 里面
        drafts = split_policy_text(text, page=page)

        local_rows: dict[int, DocumentChunk] = {}

        for index,draft in enumerate(drafts):
            chunk=DocumentChunk(
                document_id=document.id,
                parent_id=None,
                ordinal=ordinal,
                section=draft.section,
                page=draft.page,
                content=draft.content,
                is_parent=draft.is_parent,
                token_count=len(draft.content),
                metadata_json=draft.metadata,
            )


            chunk_rows.append(chunk)
            session.add(chunk)
            session.flush()
            local_rows[index] = chunk
            # 父块的id 对应不上
            if draft.parent_index is not None:
                print("parent_index",draft.parent_index)
                print("parent_id",local_rows[draft.parent_index].id)
                chunk.parent_id = local_rows[draft.parent_index].id
            ordinal+=1
        print("开始打印字典中的内容")
        print(local_rows)
    child_chunks=[chunk for chunk in chunk_rows if not chunk.is_parent]
    chunk_num = len(child_chunks)
    print("该文档子块的数量是",chunk_num)

    # 将这些子块全部进行向量化然后保存到向量数据库中
    vectorService = VectorStoreService()
    # async 方法中，如果需要调用异步方法，要进行await
    await vectorService.add_chunks(document,child_chunks)

    document.chunk_count = chunk_num
    document.status = DocumentStatus.ready

    session.commit()

    print("上传成功")

    return document


from pathlib import Path
from pypdf import PdfReader

def extract_pages(path: Path) -> list[tuple[int | None, str]]:
    suffix=path.suffix.lower()
    pages: list[tuple[int | None, str]] = []
    if suffix == ".pdf":

        pdf_pages = PdfReader(path).pages
        for index, page in enumerate(pdf_pages, start=1):
            # pypdf 对空白页/扫描页会返回 None，直接跳过，避免下游切块时 TypeError
            text = page.extract_text() or ""
            if text.strip():
                pages.append((index, text))
    elif suffix == ".docx":
        from docx import Document as DocxDocument
        document = DocxDocument(str(path))
        content = "\n".join([paragraph.text for paragraph in document.paragraphs])
        pages.append((None, content))
    else:
        txtPath = Path(str(path))
        content = txtPath.read_text(encoding="utf-8")
        pages.append((None, content))

    return pages


from pathlib import Path
from typing import List, Tuple, Optional

from langchain_core.documents import Document
from docx import Document as DocxDocument


def extract_pages2(path: Path) -> List[Tuple[Optional[int], str]]:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        # 使用 PyPDFLoader 替代直接 PdfReader
        loader = PyPDFLoader(str(path))
        docs: List[Document] = loader.load()
        return [(doc.metadata["page"], doc.page_content) for doc in docs]

    if suffix == ".docx":
        # docx 没有官方loader，保留原有解析逻辑（维持原行为：全部合并、page=None）
        document = DocxDocument(str(path))
        full_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return [(None, full_text)]

    # 普通文本文件，使用 TextLoader
    loader = TextLoader(str(path), encoding="utf-8")
    docs: List[Document] = loader.load()
    return [(None, docs[0].page_content)]


async def delete_document(session: Session, document: PolicyDocument) -> None:
    await VectorStoreService().delete_document(document.id)
    path = Path(document.stored_path)
    session.delete(document)
    session.commit()
    if path.exists():
        path.unlink()

# 这个方法一调用，所有的文档的向量数据库都要重新做一遍
async def rebuild_index(session: Session) -> int:
    # 先从数据库中查询所有的子块信息
    query = session.query(DocumentChunk, PolicyDocument) \
        .join(PolicyDocument, DocumentChunk.document_id == PolicyDocument.id) \
        .filter(DocumentChunk.is_parent.is_(False))

    rows = list(query.all())
    store = VectorStoreService()
    await store.reset()
    # 循环添加向量数据库
    grouped: dict[str, tuple[PolicyDocument, list[DocumentChunk]]] = {}
    # 将mysql中的数据封装到了一个grouped的字典中
    for chunk, document in rows:
        document_id = document.id
        if not document_id in grouped.keys():
            grouped[document_id] = (document, [])
        grouped[document_id][1].append(chunk)

# 将grouped 中的数据保存到向量数据库中
    for document, chunks in grouped.values():
        await store.add_chunks(document, chunks)
        document.index_version += 1
    session.commit()
    # 返回添加的条数
    return len(rows)