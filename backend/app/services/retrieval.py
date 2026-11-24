from dataclasses import dataclass
from typing import Any, List
from sqlalchemy.orm import Session
from app.schemas import RetrievalFilters
from app.services.model_factory import create_chat_model, invoke_text
from app.services.vector_store import VectorStoreService
import asyncio
import re
from app.services.pipeline_utils import reciprocal_rank_fusion, normalize_logit, filter_evidence
from sqlalchemy import select
from app.models import DocumentChunk, PolicyDocument

@dataclass
# 数据结构体 作用: 统一对外输出格式,上层接口只接受这个对象
class RetrievalResult:
    query: str  # 经过大模型改写后的检索问句
    candidates: list[dict[str, Any]] # RRF 融合之后的**原始切片候选（还是子块，没有补齐父上下文）**
    evidence: list[dict[str, Any]] # 最终送给 LLM 的参考资料（补齐父章节、重排序、过滤完成）
    refused: bool  #True = 找不到相关资料，LLM 禁止编造答案
    refusal_reason: str | None
    trace: dict[str, Any]  # 全链路中间数据，排查 bug、观察召回效果必备

# 工具函数:根据过滤条件，过滤掉查询出来的向量结果
async def apply_metadata_filters(vector_results, filters):
    rows=vector_results
    if filters.topic:
        rows = [result for result in rows if result['metadata']['topic']==filters.topic ]
    print("过滤完topic之后的数据",rows)
    if filters.effective_before:
        rows = [result for result in rows if  result['metadata']['effective_date'] <= filters.effective_before.isoformat() ]
    print("过滤完时间之后的数据", rows)
    return rows

# 扩充父块上下文,根据证据数据获取父块信息
async def expand_parent_context(session, evidence):
    parent_ids=[]
    for item in evidence:
        parent_ids.append(item['metadata']['parent_id'])
    if not parent_ids:
        return evidence

    # 通过sqlalchemy 查询父块信息
    chunks_list=session.query(DocumentChunk).filter(DocumentChunk.id.in_(parent_ids)).all()
    #
    #改成异步设这样的
    # stmt = select(DocumentChunk).where(DocumentChunk.id.in_(parent_ids))
    # result =  session.execute(stmt)      # await session.execute(stmt)
    # chunks_list = result.scalars().all()

    # 将这个list 信息保存成 字典   {父块id-> 父块信息}
    parents=dict()
    for chunk in chunks_list:
        parents[chunk.id]=chunk
    print("封装父块信息如下:")
    print(parents)

    # set 集合中存储的都是父id,已经在某个子块中添加过的父块信息，其他子块不需要再添加了
    seen_parents = set()
    # 将每一个包含父块和子块信息的 字典，放入到这个集合中，方便  return 返回
    expanded: list[dict[str, Any]] = []
    # 循环每一个子块，给子块添加对应的父块信息
    for item in evidence:
        # item 其实就是milvus中的一个子块
        parent_id = item["metadata"].get("parent_id")
        # 根据字典获取父块信息，其实父块信息来自于数据库
        parent = parents.get(parent_id)
        # 重点：同一个父文档只加入一次，避免重复文本
        if parent and parent_id not in seen_parents:
            item = {
                **item,
                "content": parent.content, # 把短切片替换成完整章节
                "metadata": {
                    **item["metadata"],
                    "section": parent.section or item["metadata"].get("section", ""),
                    "page": parent.page or item["metadata"].get("page", 0),
                    "context_chunk_id": parent.id,
                },
            }
            seen_parents.add(parent_id)
            expanded.append(item)
    return expanded

async def retrieve(
    session: Session,
    question: str,
    filters: RetrievalFilters,
    top_k: int = 8,  # top_k：多路融合之后保留多少候选切片
    evidence_top_k:int =4,  # evidence_top_k：最终送给 LLM 最多几条证据
    min_score: float = 0.4,  # min_score=0.4：最低相关性阈值，低于直接丢弃
    mode:str="full"  # `mode` 三种模式：vector/hybrid_rerank/full
) -> RetrievalResult:

    # 第一:查询改写rewrite_query,查询milvus数据
    new_question=await rewrite_query(question)

    # 第二: 向量库milvus检索
    vector_results=await VectorStoreService().search(
        new_question,
        top_k * 2,  # 多召回一倍，预留过滤损耗
        # `top_k*2` 设计思路：我最后只要 8 条候选，先召回 16 条，过滤删掉一批后仍然有充足数据。
        document_ids=filters.document_ids or None
    )
    # 先过滤相似度低于阈值
    vector_results = [item for item in vector_results if item['score'] > min_score]
    # 再过滤topic、时间等元数据
    vector_results = await apply_metadata_filters(vector_results, filters)
    # 由于vector_results 里面的 source 默认是文件名，所以想将其修改为 vector
    # 标记来源，方便调试
    for item in vector_results:
        item['source'] = 'vector'
    print('-' * 20)
    print(vector_results)

    # 第三 : modl分支,m是否启用了BM25关键词检索
    if mode=="vector":  # mode="vector：只使用语义检索，不开启关键词搜索，开发调试用
        print("-"*50)
        print(vector_results)
        # keyword_list = list[dict]= []
        keyword_list = []
    #其他模型必须查询向量数据库＋bm25检索
    else:
        # 向量检索结果 + bm25检索结果 综合得分高的 作为候选数据
        keyword_list = await keyword_search(session, new_question, top_k * 2, filters)
        print('*'*20)
        print(keyword_list)


    # 第五:下面是PRF多路结果融合
    fused = [ vector_results[:top_k],keyword_list]
    rrf_list = reciprocal_rank_fusion(fused)
    # candidates 获取的是通过向量数据库召回的数据
    # 截取前top_k作为候选
    candidates = rrf_list[:top_k]
    #print(candidates)
    # 证据，所谓的证据就是候选数据打分比较高的数据
    """
    现在我们有两份列表：
    `vector_results`：向量召回结果，score 0~1
    `keyword_list`：BM25 召回结果，score 无上限

    **问题：两套分数标准不一样，不能直接相加对比！**
    RRF（倒数排名融合）：**不看分数大小，只看文档在各自列表中的排名先后**
    排名越靠前，融合之后权重越高。
    输出 `candidates`：融合排序后的子切片列表。
    """

    evidence = []
    for item in candidates:
        #分数要在0和1之间
        #score=float(item.get('score',0))
        score = max(0.0, min(1.0, float(item.get("score", 0))))
        if score >= min_score:
            # 这个分数目前来讲没有用
            item["evidence_score"] = score
            evidence.append(item)
    # 遍历融合后的候选，把低于阈值的直接剔除。此时 evidence 依旧是**短子块切片**。
    # print("打印证据")
    # print(evidence)
    # 根据子块数据获取parent_id 从而去数据库mysql查询父块信息



    evidence = await expand_parent_context(session, evidence)
    #执行完这一行：列表内`content`从小段切片 → 完整章节文本。
    # evidence 就是包含了父块信息的子块内容
    print("---------------打印最终的证据------------------")
    #print(evidence)
    # 取最大值的原因 ： 保证送入后续流程的候选文档数量足够 重排序模型一般要求输入一批候选，再从中筛出 rerank_top_k 条；
    evidence = evidence[:max(evidence_top_k, top_k)]
    if mode in ["hybrid_rerank","full"]:
        evidence=await rerank(new_question,evidence,evidence_top_k)
    else:
        evidence = evidence[:evidence_top_k]
    # 截断，并且判断是否开启重排序
    # 重排序 CrossEncoder：**粗筛之后精细打分**
    # 向量 + BM25 属于粗召回；重排是精排，判断文本真实相关性。


    # 给每一个证据重新赋予一个得分evidence_score
    """
        假如证据中有rerank_score， evidence_score=rerank_score
        假如证据中有score，        evidence_score=score
        假如证据中有rrf_score      evidence_score=rrf_score*30
        接着对 evidence_score 进行归一化处理
    """

    #统一标准化 evidence_score
    for item in evidence:
        # 优先取重排序模型输出的原始分数rerank_score（重排模型 logit 值，可正可负）
        normalized = item.get("rerank_score")
        if normalized is None:
            # 如果连 score 也没有，拿 RRF 分数 ×30。
            normalized = item.get("score", item.get("rrf_score", 0) * 30)
            """
              把最终分数钳位裁剪到 [0.0,1.0]：
                  大于 1 → 强制变成 1.0
                  小于 0 → 强制变成 0.0
              """
        item["evidence_score"] = max(0.0, min(1.0, float(normalized)))

    # 假如是full模型，将证据中比较低的得分再次过滤一下
    if mode == "full":
        evidence = filter_evidence(evidence, min_score)

    refused = True if len(evidence) == 0 else False
    refusal_reason = "没有查询到合适的数据" if refused else None

    # 11.组装 trace 日志 + 判断是否拒答
    trace = {
        "original_query": new_question,
        # rewritten_query 与 original_query 同值：前端评估页读取 rewritten_query，聊天 SSE 读取 original_query
        "rewritten_query": new_question,
        "vector_results": vector_results,
        "final_evidence": evidence,
        ##
        "keyword_results": keyword_list,
        "fused_results": candidates,
        "refusal_reason": refusal_reason,

    }

    return  RetrievalResult(
        query=new_question,
        candidates=candidates,
        evidence=evidence,
        refused=refused,
        refusal_reason=refusal_reason,
        trace=trace
    )


#  配合第四步骤
#停用词集合
STOP_WORDS = {"的", "了", "是", "在", "和", "有", "就", "都", "而", "及"}
# 正则：只允许纯中文 或者 纯字母数字，不能混杂符号
valid_pat = re.compile(r"^([\u4e00-\u9fff]+|[A-Za-z0-9]+)$")  #u4e00-u9fff是正则表达式的范围,代表的匹配单个简体、繁体中文汉字
#作用：清洗文本，给 BM25 提供干净的检索词。
def tokenize_chinese(text:str) ->list[str]:
    """
    中文文本分词
    :parm text:原始输入文本
    :return:过滤后的token列表
    """
    text_low = text.lower()
    # lcut_for_search：搜索模式，会把长词再细切，适合检索场景
    import jieba

    words = jieba.lcut_for_search(text_low)
    word_list=[]
    for word in words:
        # 1.正则校验；2.不要停用词；3.长度大于1，过滤单字
        if valid_pat.fullmatch(word) and word not in STOP_WORDS and len(word) > 1:
            word_list.append(word)
    return word_list

# 第四: keyword_search BM25 关键词检索，单独拿出来讲
async def keyword_search(
    session: Session,
    query: str,
    top_k: int,
    filters: RetrievalFilters,
) -> list[dict[str, Any]]:
    #将两个表进行关联查询
    statement = (
        select(DocumentChunk, PolicyDocument)
        .join(PolicyDocument, DocumentChunk.document_id == PolicyDocument.id)
        .where(DocumentChunk.is_parent.is_(False))
    )
    # 继续拼接查询条件，将查询条件拼接到 statement里面
    if filters.document_ids:
        statement = statement.where(DocumentChunk.document_id.in_(filters.document_ids))
    if filters.topic:
        statement = statement.where(PolicyDocument.topic == filters.topic)
    if filters.effective_before:
        statement = statement.where(
            PolicyDocument.effective_date <= filters.effective_before
        )
    # 满足过滤条件的子块信息
    # 此处可以不转换为list
    rows = list(session.execute(statement).all())
    print(rows)
    if not rows:
        return []
    # 存放切分完之后的所有结果
    corpus: List[List[str]] = []
    for chunk in rows:
        # chunk 是一个元组，这个元组中只有一个对象 DocumentChunk
        print(chunk[0].content)
        corpus.append(tokenize_chinese(chunk[0].content))
    # print(chunk.content)
    # 使用bm25打分
    print("corpus的长度", len(corpus))
    # 将问题分词，然后计算每个词 和 这个问题的得分，他们的得分和词是一对一的关系
    from rank_bm25 import BM25Okapi

    bm25_model = BM25Okapi(corpus)
    scores = bm25_model.get_scores(tokenize_chinese(query))
    print(scores)
    # 此处的分数是bm25的分数,, 分数由高到低排序
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
    print(ranked)
    # 每一个分数对应的信息封装起来返回即可
    # ranks((下标,分数))
    result_list = []
    for index, score in ranked:
        # print(index,score)
        if score > 0:
            document_chunk = rows[index][0]
            policy_document = rows[index][1]
            result_list.append({
                "chunk_id": document_chunk.id,
                "content": document_chunk.content,
                "score": float(score),
                "source": "bm25",
                "metadata": {
                    "document_id": policy_document.id,
                    "filename": policy_document.filename,
                    "topic": policy_document.topic or "",
                    "section": document_chunk.section or "",
                    "page": document_chunk.page or 0,
                    "parent_id": document_chunk.parent_id or "",
                },
            })
    return result_list

#获取重排序的模型对象
from functools import lru_cache
from app.config import get_settings

@lru_cache
def get_reranker():
    # CrossEncoder 依赖 sentence-transformers + torch，体积较大。
    # 改为惰性导入：没安装时抛出异常，由 rerank() 的兜底逻辑降级为 RRF 分数，不影响主流程。
    from sentence_transformers import CrossEncoder
    model_name = get_settings().reranker_model
    return CrossEncoder(model_name,local_files_only=True)

# 就是根据问题，对证据进行重排序
async def rerank(query: str, candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates:
        return []
    settings=get_settings()
    if not settings.enable_reranker:
        return candidates[:top_k]
    try:
        # to_thread：CrossEncoder是同步模型，丢线程池，不阻塞异步主流程
        scores=await asyncio.to_thread(
            get_reranker().predict,
            [(query,item['content']) for item in candidates]
        )

        print('开始打印分数：')
        # [0.9990607 0.4304046 0.779119 ]
        print(scores)

        # candidates 是一个列表，列表本身可以排序，但是目前这个列表中没 重排序得到的分数
        # 重排序的分数写入字典
        for item, score in zip(candidates, scores):
            # raw 原始的意思
            score = float(score)
            item['rerank_raw_score'] = score
            # 将原始得分进行归一化处理，就变成了重排序得分
            item['rerank_score'] = normalize_logit(score)
        # 根据重排分数重新倒序排列，截取top_k
        return sorted(
            candidates, key=lambda item: item.get('rerank_score', 0), reverse=True
        )[:top_k]
    except Exception as e:
        print("*"*50,e)
        # 异常兜底策略：重排模型崩了也不能让整个检索报错
        for item in candidates:
            # 拿之前多路召回融合得到的 rrf_score，简单放大，上限钳位到1.0，充当伪rerank_score  所得结果不会超过1
            item["rerank_score"] = min(1.0, item.get("rrf_score", 0) * 30)
        return candidates[:top_k]


async def rewrite_query(question: str) -> str:
    """把口语化问题改写成更适合检索的查询；失败时退回原问题。
    用户原始问句经常是口语化：
    `我现在大二，想换个专业，要准备啥材料呀？`
    大模型精简为：`本科二年级学生转专业申请材料`
    疑问句→陈述句，更利于检索。调用失败自动降级使用原问题。
    """
    prompt=f"""
       将下面的学生口语化提问改写为一个适合教务政策库检索的简洁中文查询。
        不得添加问题中没有的专业、学院、年份或条件，只输出改写结果。
        问题：{question}
    """
    try:
        model = create_chat_model(get_settings(),temperature=0)
        answer, _ = await invoke_text(model, prompt)
        # return answer.strip()[:500] or question
        return answer
    except Exception:
        return question
