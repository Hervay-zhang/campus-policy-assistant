from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from app.config import get_settings
from app.database import SessionLocal
from app.models import SystemSetting

# 给定一个key值，通过key值去数据库查询对应的value值，如果没有查询到，返回默认值
def read_model_setting(key: str, default: str) -> str:
    # 此处的session 也可以通过接口 传递过来
    with SessionLocal() as session:
        systemSetting=session.get(SystemSetting,key)
        if systemSetting and systemSetting.value:
            return systemSetting.value

    return default


def create_chat_model(settings,temperature=0.5):
    # 此处是.env中的设置，可以理解为出场设置
    s = settings
    # 从数据库获取的数据，相当于是用户设置
    model_name=read_model_setting("model_provider",s.model_provider)
    if model_name=='deepseek':

        if not s.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置")
        model = init_chat_model(
            model_provider="openai",
            api_key=s.deepseek_api_key,
            base_url=read_model_setting("model_base_url", s.deepseek_base_url),
            temperature=temperature,
            model=read_model_setting("model_name", s.deepseek_model),
        )
    else:
        from langchain_ollama import ChatOllama

        model = ChatOllama(
            model=read_model_setting("model_name", s.ollama_model),
            base_url=read_model_setting("model_base_url", s.ollama_base_url),
            temperature=temperature,
            num_gpu=0
        )

    return model


async def invoke_text(model,question):
    response= await model.ainvoke(question)
    if not isinstance(response,AIMessage):
        raise TypeError(f"类型不支持，我需要的是Aimessage,而你是{type(response).__name__}")
    return response.text,dict(response.usage_metadata)