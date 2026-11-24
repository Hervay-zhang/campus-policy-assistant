from pathlib import Path


def format_documents(documents):
    formatted_documents = []

    for index, document in enumerate(documents, start=1):
        # print(document.metadata)
        source = document.metadata.get("source", "未知文件")
        file = Path(source)
        # print(file.name)
        page = document.metadata.get("page")

        source_text = file.name
        if page is not None:
            source_text += f"，第 {page + 1} 页"

        formatted_documents.append(
            f"[资料 {index}]\n"
            f"来源：{source_text}\n"
            f"内容：{document.page_content}"
        )

    return "\n\n".join(formatted_documents)


def build_sources(documents):
    sources = []
    seen = set()

    for document in documents:
        file_name = document.metadata.get("source", "未知文件")
        path=Path(file_name)
        fileName=path.name
        page = document.metadata.get("page")
        source_key = (fileName, page)


        if fileName in seen:

            continue

        seen.add(source_key[0])
        print(file_name+"已经添加进来")
        sources.append(
            {
                "file_name": fileName,
                "page": page + 1 if page is not None else None,
            }
        )

    return sources