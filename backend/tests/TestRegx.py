# 标题正则，和项目保持一致
import re

HEADING_PATTERN = re.compile(
    r"(?m)^([第][一二三四五六七八九十百]+[章节条]\s*.*|[一二三四五六七八九十]+[、.]\s*.*|\d+[.、]\s*.*)$"
)

# 测试文本：包含前置导语、第X章、中文数字序号、阿拉伯数字序号，普通段落
test_doc = """
为落实相关工作，特制定本管理办法。

第一章 总体规定
本章节用于说明制度适用范围与基本原则。
本办法适用于公司各业务部门。

一、适用对象
全体在职员工均需要遵守本管理办法。

二. 时间要求
本办法自发布之日起正式生效。

1. 职责划分
行政部门负责制度宣贯与监督执行。

2、违规处理
出现违规行为，将按照公司规定予以处置。

第三章 附则
本办法由行政部负责解释。
"""
print("==================== 1. finditer：获取全部标题匹配对象（matches） ====================")
match_list=list(HEADING_PATTERN.finditer(test_doc))
for index,match in enumerate(match_list, start=1):
    print(match)
    print(f"\nmatch[{index}]:")
    print(f"  span() = {match.span()}")
    print(f"  start()= {match.start()}, end()={match.end()}")
    # group(0)：Python 正则固定含义，整个正则完整匹配到的全部文本，永远存在，不受括号影响。
    # group(1)：你写的唯一一对圆括号 ( ... ) 捕获到的内容。
    print(f"  group(0)={repr(match.group(0))}")
    print(f"  group(1)={repr(match.group(1))}")

print("\n==================== 2. fullmatch：逐行判断某一行是不是标题 ====================")
for line in test_doc.splitlines():
    match = HEADING_PATTERN.fullmatch(line)
    if match:
        print(f"{line} 匹配成功",match.group(1))
        print()
    else:
        print(f"{line} 匹配失败")
        print()

print("\n==================== 3. 模拟 split_policy_text 内部逻辑：切分 sections（标题+正文片段） ====================")
if not match_list:
    sections = [(None, test_doc)]
else:
    sections=[]
    if match_list[0].start() > 0:
        content = test_doc[0:match_list[0].start()]
        sections.append((None,content))
    for index,match in enumerate(match_list):
        if index + 1 < len(match_list):
            next_title_start=match_list[index+1].start()
        else:
            next_title_start=len(test_doc)
        content=test_doc[match.start():next_title_start]
        sections.append((match.group(1),content))

    for i, (sec_title, sec_body) in enumerate(sections):
        print(f"\n==== section[{i}] 标题={repr(sec_title)} ====")
        print(f"section正文片段:\n{sec_body}")


print('------------------repr的使用-------------')
s = "一、适用对象\n"
print(s)
print(repr(s))



