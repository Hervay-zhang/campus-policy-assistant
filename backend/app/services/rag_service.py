import time
from dataclasses import dataclass
from typing import Any
from sqlalchemy.orm import Session
from app.config import get_settings
from app.schemas import RetrievalFilters
from app.services.model_factory import create_chat_model, invoke_text
from app.services.retrieval import retrieve

REFUSAL_TEXT = (
    "根据当前教务政策库，暂时找不到足够可靠的条款依据。请补充具体事项，"
    "例如“转专业”“补考与重修”“国家奖学金”“毕业与学位”等。"
)
# 用户的问题，rag回答的内容需要封装成这个类 返回
@dataclass
class RAGAnswer:
    answer:str  # 最终回答文本
    refused: bool   # 是否拒答
    citations: list[dict[str, Any]]  # 引用列表
    trace: dict[str, Any]  # 检索和引用校验调试信息
    latency_ms: int  # 本次回答耗时
    token_usage: dict[str, Any]  # 模型 Token 使用量

import re
CITATION_PATTERN = re.compile(r"\[(\d+)\]")
def validate_citations(answer: str, evidence: list[dict]) -> tuple[str, list[int]]:
    """
    校验回答里的角标引用标记 [数字]，过滤无效引用；返回清理后的回答 + 合法引用编号列表
    :param answer: LLM输出的回答文本，里面带有 [1][2] 这类引用标记
    :param evidence: RAG检索出来的证据片段列表，长度N，合法引用编号是 1~N
    :return: (清理后的回答文本, 真正有效的引用id有序列表)
    """
    # 提取answer中的序号
    r1=CITATION_PATTERN.findall(answer)
    cited=set()
    for value in r1:
        cited.add(int(value))
    print(cited)
    # 根据证据中的list的长度，获取一个set集合
    valid=set()
    for i in range(1,len(evidence)+1):
        valid.add(i)
    print(valid)
    # 不合理的编号   就是模型中有，但是不应该存在的
    invalid = cited - valid
    print("/"*60)
    print(invalid)
    if invalid:
        for index in invalid:
            answer=answer.replace(f'[{index}]','')
    print("+"*30)
    print(answer)
    # set集合会自动从小到大排序，添加完list之后依然可以排序，所以此处不用sorted
    return answer, list(cited & valid)

# if __name__ == '__main__':
#     validate_citations('向量数据库[2]，大模型幻觉[4]，Reranker[3]',[{},{},{},{}])
#
#     set1=list({1,2,3,5,4})
#     print(set1)

# answer_question  回答    --->  retrieve  检索
# 先检索找证据，然后才能调用大模型
async def answer_question(
    session: Session,  # 数据库会话
    question: str,  # 用户问题
    filters: RetrievalFilters | None = None,  # 检索过滤条件
    top_k: int | None = 8,  # 召回数量
    rerank_top_k: int | None = 4,  # 重排序保留数量
    min_score: float | None = 0.25,  # 最低证据分数
    mode: str = "full",  # 检索模式
) -> RAGAnswer:
    started = time.perf_counter()  #  统计整个 RAG 回答耗时。
    #time.perf_counter() 是 Python 高精度性能计时器
    print("-"*50)

    retrieve_result= await retrieve(
        session, question, filters, top_k, rerank_top_k, min_score, mode
    )
    print("@"*20)

    #证据不足时拒答
    if retrieve_result.refused:
        return RAGAnswer(
            REFUSAL_TEXT,
            True,
            [],
            retrieve_result.trace,
            int((time.perf_counter() - started) * 1000),
            {},
        )
        # 代码如果能到这里，说明问题有检索的结果
    evidences = retrieve_result.evidence
    contexts = []
    for index, evidence in enumerate(evidences, start=1):
        content = evidence['content']
        page = evidence['metadata']['page']
        section = evidence['metadata']['section']
        filename = evidence['metadata']['filename']
        contexts.append(f"[{index}] 文档：{filename},章节：{section},页码：{page}\n{content}")
    context = "\n\n".join(contexts
    )
    print(content)

    prompt = f"""你是广东工业大学教务政策知识库助手（校园百事通）。必须遵守：
    1. 只能依据“教务政策证据”回答，不得使用外部知识补充政策内容。
    2. 每个包含政策事实、数字、日期、对象或条件的句子末尾标注引用编号，如[1]。
    3. 证据没有说明的内容，明确回答“资料未说明”。
    4. 不得编造政策名称、办理条件、经办部门、时间节点或引用。
    5. 回答面向在校学生，用简明中文说清适用对象、所需材料和办理时间。

    教务政策证据：
    {context}

    用户问题：{question}
    """

    llm = create_chat_model(get_settings(), temperature=0)
    answer, usage = await invoke_text(llm, prompt)
    print(answer,usage)
    # 将结果和之前的证据进行匹配，过掉中结果中不合理的编号
    answer, list_xh = validate_citations(answer, evidences)
    # 收集该答案对应的引用信息
    citations = []
    for index in list_xh:
        item = evidences[index - 1]
        citations.append(
            {
                "chunk_id": item["chunk_id"],
                "document_id": item["metadata"].get("document_id", ""),
                "filename": item["metadata"].get("filename", ""),
                "section": item["metadata"].get("section") or None,
                "page": item["metadata"].get("page") or None,
                "quote": item["content"][:500],
                "score": item["evidence_score"],
                "label": str(index),
            }
        )

    #  拒答判定分两路：
    #  1) 完整证据约束下引用被全部校验剔除，说明没有可用的证据
    #  2) 模型自己判定证据不足（答案以“资料未说明”开头），此时即使带了引用编号，
    #     也是把不相关条款硬挂上去了，应记为拒答并剔除引用
    model_says_unknown = answer.strip().startswith("资料未说明")
    if mode == 'full' and not citations:
        answer = REFUSAL_TEXT
        citations = []
        refused = True
    elif model_says_unknown:
        citations = []
        refused = True
    else:
        refused = False



    trace = retrieve_result.trace
    trace["citation_validation"] = {
            'cited_indexes': list_xh,
            'valid': not refused
        }

    ragAnswer=RAGAnswer(
        answer,
        refused,
        citations,
        trace,
        int((time.perf_counter() - started) * 1000),
        usage
    )
############################################################

    #在返回之前,将信息保存到数据库中

    # 会重复在数据库中加载,,这个我先注销了
    # await save_chat(session,question,ragAnswer,None)
    return ragAnswer

from datetime import datetime, timezone

from app.models import ChatMessage, Citation, Conversation


async def save_chat(
    session: Session,
    question: str,
    result: RAGAnswer,
    conversation_id: str | None,
) -> tuple[Conversation, ChatMessage]:
    # print(f"[SAVE_CHAT_DEBUG] 传入conversation_id={conversation_id}")

    #保存会话数据
    if conversation_id:
        conversation= session.get(Conversation, conversation_id)
    else:
        conversation= None

    if not conversation:
        conversation = Conversation(title=question[:50])
        session.add(conversation)
        #刷新一下就会出现id
        session.flush()

    #先保存用户提出的问题,用户的问题也是消息
    #保存消息数据
    conversation.updated_at = datetime.now(timezone.utc)

    userMessage= ChatMessage(
            conversation_id=conversation.id,
            role="user",
            content=question,
        )
    session.add(userMessage)
    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=result.answer,
        refused=result.refused,
        latency_ms=result.latency_ms,
        token_usage=result.token_usage,
        trace=result.trace,
    )
    session.add(assistant_message)
    session.flush()

    for item in result.citations:
        session.add(
            Citation(
                message_id=assistant_message.id,
                chunk_id=item["chunk_id"],
                label=item["label"],
                quote=item["quote"],
                score=item["score"],
            )
        )
    session.commit()
    return conversation, assistant_message