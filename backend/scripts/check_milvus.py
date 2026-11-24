import asyncio

from app.services.vector_store import VectorStoreService

def test_query():
    service=VectorStoreService()
    documents_ids=["a4a8a3de-8d05-452d-966e-84d077dd2566"]
    result=asyncio.run(service.search("转专业需要满足哪些条件?",3,documents_ids))
    print(result)

def test_delete():
    service=VectorStoreService()
    document_id="a4a8a3de-8d05-452d-966e-84d077dd2566"
    asyncio.run(service.delete_document((document_id)))

def test_reset():
    service=VectorStoreService()
    asyncio.run(service.reset())

if __name__ == "__main__":
    # test_query()
    # test_delete()
    test_reset()