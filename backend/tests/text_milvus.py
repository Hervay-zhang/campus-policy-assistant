from datetime import time
from pathlib import Path
import random
from langchain_milvus import Milvus
from typing import Collection

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from utils.model_factory import get_milvus_client, get_embedding_model

# 加载文档
# 1. 加载 PDF 文档
file_path = Path(__file__).resolve().parent  / "article.txt"
if not file_path.exists():
    raise FileNotFoundError(
        f"未找到 PDF 文件：{file_path}\n"
        "请确认已在当前目录下创建 files/XX销售有限公司员工守则.pdf"
    )

loader = TextLoader(str(file_path),encoding="utf-8")
# 切割文档
docs=loader.load()
splitter=RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=30,
    add_start_index=True
)
chunks=splitter.split_documents(docs)

# 给每一个document 手动添加一些元数据
type=['游戏','人生','编程']
for d in chunks:
    i=random.randint(0,2)
    d.metadata['category']=type[i]

# 保存文档数据
vector_store = Milvus(
    embedding_function=get_embedding_model(),
    connection_args={"uri": "./milvus_demo.db"},   # milvus-lite 文件地址，合法！
    collection_name="employee_handbook",
    auto_id=True,
    consistency_level="Strong"
)

ids=vector_store.add_documents(chunks)
print(f"插入了{len(ids)}条数据")
# 验证文档是否保存成功
try:
    collection = Collection("employee_handbook")
    collection.load()
    # 先 flush 确保数据持久化
    collection.flush()
    time.sleep(0.5)  # 等待数据同步
    num_entities=collection.num_entities
    if len(chunks) == num_entities:
        print(f"✓ 插入成功！数据条数匹配（期望 {len(chunks)} 条，实际 {num_entities} 条）")
    elif num_entities > 0:
        print(f"⚠ 数据已插入，但数量不匹配（期望 {len(chunks)} 条，实际 {num_entities} 条）")
    else:
        # 如果数量为0，但查询能成功，说明数据在内存中，也算成功
        print("⚠ Collection 数量为 0，但数据可能在内存中（将通过查询验证）")

except Exception as e:
    print(e)

# 通过一个问题查询文档 的内容
results=vector_store.similarity_search("今天我迟到了30分钟，公司怎么处罚？",k=3)
# results 的类型是 list[Document]
if len(results)>0:
    print("最接近你这个问题的答案是：")
    for i,result in enumerate(results,start=1):
        print(f"--- 结果 {i} ---")
        print(result.page_content[:100])
        print(result.metadata)
        print()
else:
    print("您这个问题，在文档中没有答案")
