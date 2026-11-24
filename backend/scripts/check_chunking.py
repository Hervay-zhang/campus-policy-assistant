from pathlib import Path

from app.services.chunking import _windows, _windows2, split_policy_text, ChunkDraft
from app.services.document_service import extract_pages, extract_pages2


def main(sample_path):
	pages = extract_pages2(sample_path)
	# [(1,"xxxx"),(2,"xxxxxx"),()]
	print("页数：", len(pages))
	print("第一页页码：", pages[0][0])
	print("第一页文本：", pages[0][1])

def  check_window():
	test_text = """人工智能是研究如何让机器模拟人类智能的技术。
	它涵盖大模型、自然语言处理、计算机视觉等多个方向。
	大模型可以理解文本，回答问题，辅助文档处理。
	在RAG系统中，文本分块质量直接影响检索与问答效果！
	不合理的切分会把完整语义拆碎，降低最终答案的准确性。"""
	list=_windows2(test_text,size=80,overlap=20)
	for chunk in list:
		print(chunk)

def check_split_policy_text():
	sample_path=Path("../sample_data/广东工业大学本科毕业论文（设计）管理办法.pdf")
	pages = extract_pages(sample_path)

	for index,pageTuple in enumerate(pages):
		page=pageTuple[0]
		content=pageTuple[1]
		drafts:list[ChunkDraft]=split_policy_text(content,page,1200,100,10)
		parents = [chunk for chunk in drafts if chunk.is_parent]
		children = [chunk for chunk in drafts if not chunk.is_parent]
		print(f"第{page}页")
		print("总块数：", len(drafts))
		print("父块数：", len(parents))
		print("子块数：", len(children))
		print("以下是当前页切分的情况:")
		print(drafts)



if __name__ == '__main__':
	# list=[
	# 	Path("../sample_data/广东工业大学本科毕业论文（设计）管理办法.pdf"),
	# 	Path("../sample_data/广东工业大学本科生学籍管理规定.docx"),
	# 	Path("../sample_data/广东工业大学本科生转专业管理办法.txt")
	# ]
	# for sample_path in list:
	# 	main(sample_path)

	#check_window()
	check_split_policy_text()
