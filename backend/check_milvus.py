import asyncio

from app.services.vector_store import VectorStoreService

if __name__ == "__main__":
    # service=VectorStoreService()
    # document_ids=["a4a8a3de-8d05-452d-966e-84d077dd2566"]
    # result = asyncio.run(service.search("青年人在这里可以申请人才公寓吗?", 3, document_ids))
    # print(result)

    service = VectorStoreService()
    # document_ids = ["a4a8a3de-8d05-452d-966e-84d077dd2566"]
    asyncio.run(service.search("青年人在这里可以申请人才公寓吗?", 3))
