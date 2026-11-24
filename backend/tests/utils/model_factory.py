import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores.milvus import Milvus
from pymilvus import connections
from pymilvus.orm import utility


def get_deepSeek_model(temperature:float=0.7):
	load_dotenv()
	model = init_chat_model(
		model="deepseek-v4-flash",
		model_provider="openai",
		base_url=os.getenv("DEEPSEEK_BASE_URL"),
		api_key=os.getenv("DEEPSEEK_API_KEY"),
		temperature=temperature
	)
	return model

def get_embedding_model():
	embeddings_model = DashScopeEmbeddings(
		model="qwen3.7-text-embedding",  # 通义千问最新的向量模型
		dashscope_api_key="sk-ws-H.EHXIYPR.kY1M.MEUCIBCVmczsf029b7xFzMhkgA1AZiRzY2FOiaqb8XtbBfgXAiEAkDehjjapBf32DNaWKjYtKxnNMF83mdXq4LDZxGGWALs"
	)
	return embeddings_model

# 获取milvus对象   传参：uri 表名  是否删除表名
def get_milvus_client(collection_name,is_delete,uri="http://localhost:19530",connect_name="default"):
	# 得到milvus的客户端
	try:

		if not connections.has_connection(connect_name):
			connections.connect(connect_name, uri=uri)
		if is_delete:
			utility.drop_collection(collection_name)
			print(f"已删除旧的 collection{collection_name}")
	except Exception as e:
		print(e)

	vector_store = Milvus(
		embedding_function=get_embedding_model(),
		collection_name=collection_name,
		connection_args={"uri": uri},
		index_params={"index_type": "HNSW",
					  "metric_type": "COSINE",
					  "params": {"M": 16, "efConstruction": 128}},
		auto_id=True
	)

	return vector_store