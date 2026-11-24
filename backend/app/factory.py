from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import documents, chat, configuration, evaluation
from app.config import get_settings

settings=get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== 应用【启动时】执行，只执行一次 ==========
    print("开始执行复杂初始化……")
    print("++++++++++++++++++++++++++++++")

    from app.database import init_database

    init_database()
    yield   # ← 服务在这里正式开始接收请求



def create_app()->FastAPI:

    app = FastAPI(
        title=settings.app_name,
        description="FastAPI + LangChain 高校教务政策知识库问答系统",
        version="1.0.0",
        lifespan=lifespan
    )

    for router in (documents.router,
                   chat.router,
                   configuration.router,
                   evaluation.router):
        app.include_router(router, prefix=settings.api_prefix)

    # app.include_router(documents.router, prefix=settings.api_prefix)
    # app.include_router(chat.router, prefix=settings.api_prefix)

    @app.get("/")
    async def get_root():
        return {
            "name": settings.app_name,
            "docs": "/docs",
            "message": "服务已启动",
        }

    return app