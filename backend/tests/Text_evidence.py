answer = "RAG是检索增强生成[1]，reranker用来重排[5]。"
evidence = [{}, {}, {}]   # 共3条证据，合法编号：1,2,3

cited = {1,5}
valid = {1,2,3}
invalid = {5}

# 处理后answer变成："RAG是检索增强生成[1]，reranker用来重排。"
# 返回有效引用：[1]