#Recall@K:::RAG检索召回率
# 期望出来的结果占检索的结果比例越高，越说明检索的质量很好
# 含义：标准证据是否出现在前 K 个检索结果中。
import re


def recall_at_k(expected: list[str], retrieved: list[str], k: int) -> float:
    if not expected:
        return 1.0
    return len(set(expected) & set(retrieved[:k])) / len(set(expected))

# MRR：含义：第一个正确证据排得越靠前，分数越高。
def reciprocal_rank(expected: list[str], retrieved: list[str]) -> float:
    expected_set = set(expected)

    for rank, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in expected_set:
            return 1.0 / rank
    return 0.0

# 引用准确率 CA：catation accuracy
# 用户问了一个问题，进行向量检索，bm25 检索等
# 得到一个结果，这个结果说  引用了 哪些块信息

def citation_precision(cited: list[str], retrieved: list[str]) -> float:
    if not cited:
        return 0.0
    return len(set(cited) & set(retrieved)) / len(set(cited))



#提取关键事实
def extract_facts(text: str) -> set[str]:
    return set(
        re.findall(
            r"\d+(?:\.\d+)?(?:%|万元|元|天|日|个月|年)?|"
            r"\d{4}年\d{1,2}月\d{1,2}日",
            text,
        )
    )



# 关键事实准确率
def factual_accuracy(reference: str, answer: str) -> float:

    s1=extract_facts(reference)
    if not s1:
        return 1.0
    s2=extract_facts(answer)

    return len(s1&s2)/len(s1)



#引用覆盖率：
def citation_coverage(answer: str) -> float:
    list1=re.split(r"[。！？\n]+", answer)
    list1=[line.strip() for line in list1 if line.strip()]

    #  给每一句话进行判断，如果有数值和关键词就留下来
    factual = [
        line for line in list1 if re.search(r"\d|条件|材料|期限|标准|应当|不得|可以|学分|绩点|重修|申请",line)
    ]

    if not factual:
        return 1.0

    # 将语句中带有引用标签的语句查出来  [1] [2]
    supported=[
        line for line in factual if re.search(r"\[\d+\]", line)
    ]
    return len(supported)/len(factual)