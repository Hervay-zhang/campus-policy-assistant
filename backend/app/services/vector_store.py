from functools import lru_cache
from os import mkdir

import asyncio
from pathlib import Path


from app.config import get_settings
from app.models import PolicyDocument, DocumentChunk


@lru_cache
def get_embeddings():
    settings=get_settings()
    # 本地 ollama 嵌入模型（原 DashScope key 已失效，改用本地 ollama，维度与既有集合一致）
    from langchain_ollama import OllamaEmbeddings
    embeddings_model=OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )
    return embeddings_model

@lru_cache
def get_vector_store():
    from langchain_milvus import Milvus
    # 假如本地没有 data/milvus 文件夹
    settings=get_settings()
    settings.milvus_path.mkdir(parents=True, exist_ok=True)

    # db_url=str(settings.milvus_path)+"/milvus_demo.db"
    # 使用 settings 中的 milvus_path 定位 milvus-lite 数据文件（不要写死绝对路径，项目目录迁移后会失效）
    db_url = str(settings.milvus_path / "milvus_demo.db")
    print(db_url)
    print(Path(db_url).resolve())
    # 获取一个milvus对象
    vector_store=Milvus(
        embedding_function=get_embeddings(),
        connection_args={"uri": db_url},  # milvus-lite 文件地址，合法！
        collection_name="policy_chunks",
        auto_id=False,
        consistency_level="Strong",
        index_params = {
            "metric_type": "COSINE",  # 关键
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64}
        }
    )

    return vector_store
# 以下是 url 的方式
# def get_vector_store():
#     settings = get_settings()
#     settings.milvus_path.mkdir(parents=True, exist_ok=True)
#
#     #
#     URI = "http://localhost:19530"
#     if not connections.has_connection("default"):
#         connections.connect("default", uri=URI)
#
#
#
#     #db_uri = str(settings.milvus_path / "milvus_demo.db")
#     vector_store = Milvus(
#         embedding_function=get_embeddings(),
#         connection_args={"uri": "http://localhost:19530"},
#         collection_name="policy_chunks",
#         auto_id=False,
#         consistency_level="Strong"
#     )
#
#     return vector_store
#两种方法一种是lilvus-lite轻量级的,第二种是docker的


# 在这个类中完成 文本 插入向量数据库  查询数据库  删除内容  重置数据库等服务
class VectorStoreService:
    # 向向量数据库插入内容
    # 传递 两个参数，第一个参数是整个文档对象  第二个参数是切割之后的父子块集合
    async def add_chunks(
            self,
            document: PolicyDocument,
            chunks: list[DocumentChunk]
    ) -> None:
        if not get_settings().enable_vector_search:
            return

        # 阿里云百炼(dashscope)接口限制：单次批量输入contents数组数量不能超过20条，你传的批次大于20，返回400参数错误。
        # 含义：调用向量化接口时，一次性塞进去的文本条数 > 20，模型服务拒绝处理。阿里云百炼的向量大模型的错误，每次让它向量化，不要超过20条。

        # 将所有的子块中的内容放入到一个list集合中
        texts = [chunk.content for chunk in chunks]

        # 将所有的子块中的id放入到一个list集合中
        chunk_ids = [chunk.id for chunk in chunks]

        # 将所有的子块中的元数据放入到一个list集合中
        # 注意：每一个子块都要生成一条元数据，与 texts/chunk_ids 一一对应；
        # 不管 document.effective_date 有没有值，都要走这里，否则 chunks 非空时 metadatas 为空，zip 之后一条都写不进去。
        if document.effective_date:
            effective_date = document.effective_date.isoformat()
        else:
            effective_date = ""

        # metadata 方便将来查找
        metadatas = [
            {
                "document_id": document.id,
                "filename": document.filename,
                "topic": document.topic or "",
                "effective_date": effective_date,
                "section": chunk.section or "",
                "page": chunk.page or 0,
                "parent_id": chunk.parent_id or "",
                "chunk_id": chunk.id,
            }
            for chunk in chunks
        ]

        # 此时形成了三个list ,这三个list的长度一样，根据下标获取的内容也可以一一照应上
        # 此时可以形成拉链 zip
        from langchain_core.documents import Document

        doc_list: list[Document] = []
        vector_store = get_vector_store()
        for chunk_id, content, metadata in zip(chunk_ids, texts, metadatas):
            doc = Document(page_content=content, metadata=metadata, id=chunk_id)
            doc_list.append(doc)
            # 每凑够 10 条就批量写入一次，避免单次请求过大
            if len(doc_list) == 10:
                vector_store.add_documents(doc_list)
                doc_list = []

        # 最后一批不足 10 条的数据，也要写入向量数据库，否则会丢失
        if len(doc_list) > 0:
            vector_store.add_documents(doc_list)
            doc_list.clear()



    # 向量数据库中的内容的查询
    # 假如用户限定了使用什么文档id ,会先从metadata中获取满足条件的文档，再从这些文档中查询意思相近的内容
    async def search(
        self,query:str,top_k:int,document_ids:list[str] | None =  None
            ) ->list[dict]:
        if not get_settings().enable_vector_search:
            return []
        vector_store=get_vector_store()
        if document_ids:
            # Milvus expr表达式语法，$in
            ids_list = [f'"{x}"' for x in document_ids]
            ids = ",".join(ids_list)
            expr = f'document_id in [{ids}]'
        else:
            expr = None

        results = vector_store.similarity_search_with_score(query, top_k, expr=expr)
        # print(results)

        return [
            {
                "chunk_id": tuple[0].metadata["chunk_id"],
                "content": tuple[0].page_content,
                "metadata": tuple[0].metadata,
                "score": tuple[1],
                "source": tuple[0].metadata["filename"],
            }
            for index, tuple in enumerate(results)
        ]

    async def delete_document(self, document_id: str) -> None:
        if not get_settings().enable_vector_search:
            return
        vector_store = get_vector_store()
        expr = f'document_id == "{document_id}"'
        vector_store.delete(expr=expr)
    # 根据文档id 删除对应的向量数据
    # 将向量数据库清空
    async def reset(self) -> None:
        if not get_settings().enable_vector_search:
            return
        vector_store = get_vector_store()
        expr = f' pk > 0 '
        vector_store.delete(expr=expr)

