import asyncio
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal, settings
from app.models import SystemSetting
from app.services.model_factory import create_chat_model, invoke_text


def save_setting(session, key: str, value: str) -> None:
    row = session.get(SystemSetting, key)
    if row:
        row.value = value
    else:
        session.add(SystemSetting(key=key, value=value))


async def main() -> None:
    with SessionLocal() as session:
        save_setting(session, "model_provider", "ollama")
        save_setting(session, "model_name", "qwen2.5:7b")
        save_setting(session, "model_base_url", "http://127.0.0.1:11434")
        session.commit()
        print("已切换到 Ollama")

    model = create_chat_model(settings,temperature=0)
    print("模型对象：", type(model).__name__)

    answer, usage = await invoke_text(
        model,
        "请用一句话回答：Ollama 在 RAG 系统中负责什么？",
    )
    print("模型回答：")
    print(answer)
    print("Token 用量：", usage)


if __name__ == "__main__":
    asyncio.run(main())