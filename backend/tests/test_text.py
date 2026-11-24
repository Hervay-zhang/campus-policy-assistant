from app.services.chunking import _windows

test_text = """人工智能是研究如何让机器模拟人类智能的技术。
它涵盖大模型、自然语言处理、计算机视觉等多个方向。
大模型可以理解文本，回答问题，辅助文档处理。
在RAG系统中，文本分块质量直接影响检索与问答效果！
不合理的切分会把完整语义拆碎，降低最终答案的准确性。"""

result = _windows(test_text, size=80, overlap=20)

for idx, ck in enumerate(result):
    print(f"【chunk {idx}】\n{ck}\n")



# 【chunk 0】
# 人工智能是研究如何让机器模拟人类智能的技术。
# 它涵盖大模型、自然语言处理、计算机视觉等多个方向。
# 大模型可以理解文本，回答问题，辅助文档处理。
#
# 【chunk 1】
# 可以理解文本，回答问题，辅助文档处理。
# 在RAG系统中，文本分块质量直接影响检索与问答效果！
# 不合理的切分会把完整语义拆碎，降低最终答案的准确性。