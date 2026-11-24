from app.services.metrics import recall_at_k, reciprocal_rank, citation_precision, factual_accuracy, citation_coverage

expected = ["chunk-a", "chunk-c"]
retrieved = ["chunk-b", "chunk-a", "chunk-d", "chunk-c"]
cited = ["chunk-a", "chunk-x"]

print("Recall@k：", recall_at_k(expected, retrieved, 3))
print("MRR：", reciprocal_rank(expected, retrieved))
print("引用准确率：", citation_precision(cited, retrieved))




reference_answer = "转专业申请时间为每年4月1日至4月15日，国家奖学金标准为每生每年8000元。"
answer = "转专业申请时间为每年4月1日至4月15日，国家奖学金标准为每生每年8000元。[1]"

print("关键事实准确率：", factual_accuracy(reference_answer, answer))
print("引用覆盖率：", citation_coverage(answer))
