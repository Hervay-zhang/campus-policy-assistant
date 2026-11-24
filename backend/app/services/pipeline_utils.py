from typing import Any
# 此函数是一个综合打分的方法
def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]], k: int = 60
) -> list[dict[str, Any]]:
    # fused 这个字典中  只有一个k和一个v ，不同的k 对应不同v
    fused: dict[str, dict[str, Any]] = {}
    # 对列表中的每一个列表进行循序
    for results in result_lists:
        # 拿到的 results 其实也是一个列表  rank 此时是排名
        for rank, item in enumerate(results, start=1):
            # 获取chunk_id 当做key
            chunk_id = item["chunk_id"]
            # 如果chunk_id 不在字典列表中，说明是第一次处理
            if chunk_id not in fused:
                fused[chunk_id] = {**item, "rrf_score": 0.0, "sources": list()}
            # 计算得分  同一个 chunk，如果同时出现在 bm25 和向量两路结果，分数会叠加。
            fused[chunk_id]["rrf_score"] += 1 / (k + rank)
            # 添加来源
            fused[chunk_id]["sources"].append(item.get("source", "unknown"))

    for dict1 in fused.values():
        dict1['sources'] = list(set(dict1['sources']))
        # 此时的字典依然成型
        # 此时的字典依然成型
    print(fused)
    print('------------------------')
    print(fused.values())
    print('------------------------')
    a = sorted(fused.values(), key=lambda item: item['rrf_score'], reverse=True)
    print(a)
    return a
    # 按照得分由高到低排序
    return sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)


import math


def normalize_logit(value: float) -> float:
    return 1 / (1 + math.exp(-max(-30, min(30, value))))

def filter_evidence(evidence: list[dict[str, Any]], min_score: float) -> list[dict]:
    return [
        item for item in evidence if float(item.get("evidence_score", 0)) >= min_score
    ]