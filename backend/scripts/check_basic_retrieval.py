# import os
# # 关闭symlink警告
# os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# # 填入自己的token消除未认证请求警告（可选）
# # os.environ["HF_TOKEN"] = "hf_x"

import sys
from pathlib import Path
# 获取当前脚本所在目录 scripts
script_dir = Path(__file__).parent
# 向上一级就是 backend目录（app文件夹所在目录）
backend_root = script_dir.parent
sys.path.insert(0, str(backend_root))


import asyncio


from app.database import  SessionLocal
from app.schemas import RetrievalFilters
from app.services.retrieval import retrieve, RetrievalResult


if __name__ == '__main__':
    session=SessionLocal()
    filter=RetrievalFilters()

    # filter.topic="测试主题"
    # filter.document_ids=['f319359f-c306-435d-8135-913662f8ec03']

    result:RetrievalResult=asyncio.run(retrieve(
        session,
        #"如何加强公共数据共享和治理",
        "如何加强公共数据共享和治理",
        filter
    ))
    print("-"*20)
    print(result)