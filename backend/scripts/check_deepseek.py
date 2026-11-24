import asyncio

#解决导入的backend为模型的错误
import sys
from pathlib import Path
# parent.parent.parent 往上跳三层：scripts → backend → langchain_project
root_path = str(Path(__file__).parent.parent.parent)
sys.path.append(root_path)


from backend.app.config import get_settings
from backend.app.services.model_factory import create_chat_model, invoke_text


async def main():
    s = get_settings()
    print(s)
    model = create_chat_model(settings=s, temperature=0.7)
    content, metadata=await invoke_text(model, "使用一句话，解释一下rag是什么")
    print(content)
    print(metadata)


if __name__ == '__main__':
    # s=get_settings()
    # print(s)
    # model=create_chat_model(settings=s,temperature=0.7)
    # response=model.invoke("使用一句话，解释一下rag是什么")
    # print(response.content)
    # # content 和 text 是一样的
    # print(response.text)
    # # 元数据中一般都是消耗的token 信息
    # print(response.usage_metadata)
    asyncio.run(main())