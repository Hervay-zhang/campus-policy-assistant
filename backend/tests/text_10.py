import asyncio


from app.database import  SessionLocal
from app.schemas import RetrievalFilters
from app.services.retrieval import retrieve

if __name__ == '__main__':
    session=SessionLocal()
    filter=RetrievalFilters()

    filter.topic="测试主题"
    filter.document_ids=['6a5ed008-7685-4db0-98c5-7eaaf50f82b7']


    res=asyncio.run(retrieve(
        session,
        "租房补贴标准",
        filter
    ))
    print("====检索返回结果====")
    print(res)