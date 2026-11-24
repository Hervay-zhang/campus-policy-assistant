import asyncio
from app.database import  SessionLocal
from app.schemas import RetrievalFilters
from app.services.rag_service import answer_question
from app.services.retrieval import retrieve, RetrievalResult

if __name__ == '__main__':
	session=SessionLocal()
	filter=RetrievalFilters()

	#filter.topic="测试主题"
	#filter.document_ids=['05129ece-2292-450c-8dc9-d68f9d3739fc']

	result:RetrievalResult=asyncio.run(answer_question(
		session=session,
		question="转专业需要满足哪些条件",
		#"今晚上晚自习吗？",
		filters=filter,
		top_k=8,
		rerank_top_k=3,
		min_score=0.25
	))
	print("*"*50)
	print(result)
