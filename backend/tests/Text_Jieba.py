import re
import jieba




if __name__ == "__main__":
    s = "人工智能是未来的发展方向，2026大模型技术正在快速进步！"

    words=jieba.lcut_for_search(s)
    # 停用词集合
    STOP_WORDS = {"的", "了", "是", "在", "和", "有", "就", "都", "而", "及"}
    # 正则：只允许纯中文 或者 纯字母数字，不能混杂符号
    valid_pat = re.compile(r"^([\u4e00-\u9fff]+|[A-Za-z0-9]+)$")
    for word in words:
        if word not in STOP_WORDS and valid_pat.fullmatch(word) and len(word)>1:
            print(word,end=" ")