# 校园百事通

FastAPI、LangChain 和 Vue 知识库问答。支持文档上传与分块、关键词检索、政策引用、流式问答和评估。

配置 `backend/.env.example` 中的数据库、模型和向量存储参数。在后端运行 `pip install -r requirements.txt` 和 `uvicorn main:app --port 8000`，在前端运行 `npm ci` 和 `npm run dev`。演示环境可设置 `ENABLE_VECTOR_SEARCH=false` 和 `ENABLE_RERANKER=false`，用 BM25 检索，配合远程对话模型运行。
