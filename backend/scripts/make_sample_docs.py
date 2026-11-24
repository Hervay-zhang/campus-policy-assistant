"""生成高校教务政策示例文档（DOCX / PDF）。

用法（在 backend 目录下）：
    ..\\.venv\\Scripts\\python.exe scripts/make_sample_docs.py

脚本只负责把两份教务政策排成 docx 与 pdf，方便演示「多格式解析」：
    - 《广东工业大学本科生学籍管理规定》 -> docx
    - 《广东工业大学本科毕业论文（设计）管理办法》 -> pdf（多页，带页码）
"""
from pathlib import Path

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"

XUEJI_TITLE = "广东工业大学本科生学籍管理规定"
XUEJI_SUBTITLE = "（2025 年 7 月修订，2025 年 9 月 1 日起施行）"
XUEJI_BODY = """第一章 入学与注册
第一条 按国家招生规定录取的新生，应当持录取通知书和学校规定的有关证件，按期到校办理入学手续。因故不能按期入学者，应当事先向所在学院请假，请假期限一般不超过两周。未请假或者请假逾期未报到的，除因不可抗力等正当事由外，视为放弃入学资格。
第二条 新生入学后三个月内，学校按照招生规定进行入学资格复查，复查内容包括录取手续、身份信息、身体健康状况、前置学历等。复查合格者予以注册，取得学籍；复查不合格者，由学校区别情况予以处理，直至取消入学资格。
第三条 每学期开学初，学生应当在规定时间内到校办理注册手续。未按学校规定缴纳学费或者其他不符合注册条件的，不予注册。家庭经济困难的学生可以申请助学贷款或者其他形式资助，办理有关手续后注册。
第二章 学制与学习年限
第四条 学校本科标准学制为四年，建筑学、城乡规划、临床医学等专业标准学制为五年。学生在校最长学习年限（含休学、保留学籍）为：四年制专业六年，五年制专业七年。超过最长学习年限未完成学业的，按退学处理。
第五条 学生可以申请提前毕业。提前完成培养方案规定的全部课程、取得规定学分且平均学分绩点不低于 3.5 的，可在标准学制最后一学年的第一学期提出提前毕业申请，经学院审核、教务处批准后办理。
第三章 课程考核与成绩记载
第六条 学生应当参加培养方案规定的课程和各种教育教学环节的考核，考核成绩记入成绩册，并归入本人学籍档案。考核合格者取得该课程学分，考核不合格者按《广东工业大学本科生课程考核与成绩管理办法》办理补考或重修。
第七条 学生严重违反考核纪律或者作弊的，该课程考核成绩记为无效，并视情节给予警告、记过、留校察看直至开除学籍处分。经教育表现较好的，在毕业前可给予一次重修机会。
第四章 休学、复学与退学
第八条 学生因患病、参军入伍、创新创业或者其他正当事由可以申请休学。休学一般以一年为期，累计不得超过两年，参军入伍的休学时间不计入学习年限。休学期间保留学籍，不享受在校生待遇。
第九条 学生休学期满，应当于学期开学前向学校提出复学申请，经复查合格后方可复学。因病休学的，复学时须提交二级甲等以上医院出具的健康证明。
第十条 学生有下列情形之一的，应予退学：学业成绩未达到学校要求，经学业警示后在一个学年内仍未达到要求的；在最长学习年限内未完成学业的；休学期满逾期两周未办理复学手续的；未经批准连续两周未参加学校规定的教学活动的；本人申请退学的。
第五章 转专业与转学
第十一条 学生申请转专业按《广东工业大学本科生转专业管理办法》执行，每学年组织一次，一年级、二年级学生可以申请。
第十二条 学生因患病或者确有特殊困难，无法继续在本校学习的，可以申请转学。转学须经转出、转入学校同意，并报省级教育行政部门备案。
第六章 毕业与结业
第十三条 学生在标准学制内修完培养方案规定的全部课程，取得规定学分，德智体美劳达到毕业要求的，准予毕业，颁发毕业证书。
第十四条 学生在标准学制内修完培养方案规定的全部课程，但未取得规定学分的，准予结业，颁发结业证书。结业生可以在结业后两年内回校重修未合格课程，达到毕业要求后换发毕业证书，毕业时间按换发日期填写。
第十五条 符合学士学位授予条件的毕业生，按《广东工业大学学士学位授予工作细则》授予学士学位。
第七章 附则
第十六条 本规定由教务处负责解释。本规定自 2025 年 9 月 1 日起施行，原《广东工业大学本科生学籍管理实施细则》同时废止。"""

LUNWEN_TITLE = "广东工业大学本科毕业论文（设计）管理办法"
LUNWEN_SUBTITLE = "（2025 年修订）"
LUNWEN_BODY = """第一章 组织管理
第一条 本科毕业论文（设计）工作由教务处统一组织，各学院负责具体实施。学院应当成立毕业论文（设计）工作领导小组，负责选题审核、过程检查、答辩组织与成绩审定。
第二条 毕业论文（设计）实行指导教师负责制。每位指导教师指导的学生人数，理工类专业一般不超过 6 人，人文社科类专业一般不超过 8 人。
第二章 选题与开题
第三条 毕业论文（设计）选题应当符合专业培养目标，体现综合训练要求，原则上一人一题。确有需要多人合作完成的，须明确每人独立完成的任务与考核要求。
第四条 选题实行学院审核制度。选题确定后不得随意变更，确需变更的，须在开题后两周内提出书面申请，经指导教师同意、学院批准后调整。
第五条 开题一般在第七学期第 12 周前完成。开题报告应当包含研究背景、国内外研究现状、研究内容与方法、进度安排与参考文献，参考文献不少于 15 篇，其中外文文献不少于 3 篇。
第三章 撰写与学术规范
第六条 毕业论文（设计）正文字数要求：人文社科类专业不少于 8000 字，理工类专业不少于 10000 字，艺术设计类专业不少于 5000 字并附作品说明。
第七条 论文撰写应当符合《广东工业大学本科毕业论文（设计）撰写规范》，包括摘要、关键词、目录、正文、参考文献、致谢等部分。图表、公式、注释格式须统一。
第八条 学校统一使用论文查重系统进行文字复制比检测。文字复制比低于 20% 的，方可参加答辩；文字复制比在 20% 至 40% 之间的，须在指导教师指导下修改，复检合格后方可答辩；文字复制比高于 40% 的，延期答辩，延期时间不少于半年。
第九条 存在购买、代写、伪造数据、抄袭剽窃等学术不端行为的，毕业论文（设计）成绩记为不及格，并按《广东工业大学学术不端行为处理办法》给予相应处分；已授予学位的，学校有权撤销其学位。
第四章 答辩与成绩评定
第十条 答辩委员会由 3 至 5 名具有讲师以上职称的教师组成，其中至少 1 名为校外专家或跨学科教师。指导教师不得担任本人指导学生的答辩委员会主席。
第十一条 答辩程序包括学生陈述（不少于 10 分钟）、答辩委员提问、学生回答、委员评议与无记名投票。答辩过程应当记录并存档。
第十二条 毕业论文（设计）成绩采用百分制，由指导教师评分（占 40%）、评阅教师评分（占 20%）、答辩成绩（占 40%）三部分构成。总评成绩 60 分以下为不及格，60 至 69 分为及格，70 至 79 分为中等，80 至 89 分为良好，90 分及以上为优秀。优秀比例不超过本专业毕业生人数的 15%。
第五章 延期答辩与二次答辩
第十三条 首次答辩未通过的学生，可在当年 9 月申请二次答辩。二次答辩仍未通过的，按结业处理，可在最长学习年限内重新申请答辩。
第十四条 因参军入伍、因病休学、赴境外交流等正当事由不能按期答辩的，可申请延期答辩，延期时间一般不超过一年。
第六章 附则
第十五条 本办法由教务处负责解释。本办法自 2025 年 9 月 1 日起施行。"""


def build_docx() -> Path:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.font.size = Pt(12)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(XUEJI_TITLE)
    run.bold = True
    run.font.size = Pt(18)
    run.font.name = "黑体"

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(XUEJI_SUBTITLE).font.size = Pt(10.5)

    for line in XUEJI_BODY.split("\n"):
        line = line.strip()
        if not line:
            continue
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.line_spacing = 1.5
        paragraph.add_run(line)

    path = SAMPLE_DIR / f"{XUEJI_TITLE}.docx"
    doc.save(path)
    return path


def build_pdf() -> Path:
    import pymupdf

    font_path = "C:/Windows/Fonts/simsun.ttc"
    page_width, page_height = pymupdf.paper_size("a4")
    margin_x, margin_y = 72, 78
    font_size, line_height = 11.5, 20

    doc = pymupdf.open()
    font = pymupdf.Font(fontfile=font_path)
    max_width = page_width - margin_x * 2

    def new_page(title: str | None = None):
        page = doc.new_page(width=page_width, height=page_height)
        if title:
            page.insert_text(
                (margin_x, margin_y - 20),
                title,
                fontsize=15,
                fontname="song",
                fontfile=font_path,
            )
        return page

    def wrap(text: str) -> list[str]:
        lines, current = [], ""
        for char in text:
            if font.text_length(current + char, fontsize=font_size) > max_width:
                lines.append(current)
                current = char
            else:
                current += char
        if current:
            lines.append(current)
        return lines

    page = new_page(LUNWEN_TITLE)
    y = margin_y + 10
    for block in [LUNWEN_SUBTITLE, *LUNWEN_BODY.split("\n")]:
        block = block.strip()
        if not block:
            continue
        for line in wrap(block):
            if y > page_height - margin_y:
                page = new_page(LUNWEN_TITLE + "（续）")
                y = margin_y + 10
            page.insert_text(
                (margin_x, y),
                line,
                fontsize=font_size,
                fontname="song",
                fontfile=font_path,
            )
            y += line_height
        y += 4

    # 只保留实际用到的字形，避免把 15MB 的中文字体整份写进 PDF
    doc.subset_fonts()

    path = SAMPLE_DIR / f"{LUNWEN_TITLE}.pdf"
    doc.save(path, garbage=4, deflate=True)
    doc.close()
    return path


if __name__ == "__main__":
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    print("生成：", build_docx())
    print("生成：", build_pdf())
