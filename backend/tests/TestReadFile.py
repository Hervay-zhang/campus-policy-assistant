from pathlib import Path
from pypdf import PdfReader
pdfPath=Path("../sample_data/星河市数字政务服务和政策兑现便利化实施意见.pdf")
pages=PdfReader(pdfPath).pages
for index,page in enumerate(pages,start=1):
	print(f"第{index}页")
	print(page.extract_text())

print("-----------------pdf结束------------------------")
# 读取docx 文档
from docx import Document as DocxDocument
document = DocxDocument("../sample_data/星河市数字政务服务和政策兑现便利化实施意见.docx")
# document中是按照段落切分的，不是按照页码切分的，所以只能将数据全部拼接成一个文章

# for index,paragraph in enumerate(document.paragraphs,start=1):
# 	print(f"第{index}页")
# 	print(paragraph.text)
content="\n".join([paragraph.text for paragraph in document.paragraphs ])
print(content)
print("-----------------docx结束------------------------")

txtPath=Path("../sample_data/星河市小微企业数字化补贴细则.txt")
content=txtPath.read_text(encoding="utf-8")
print("txt文本的内容是:")
print(content)
