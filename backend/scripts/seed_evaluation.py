"""创建一份教务政策测试集，并把四种检索方案各跑一遍，用于演示横向对比。

用法（先启动后端 8002）：
    ..\\.venv\\Scripts\\python.exe scripts/seed_evaluation.py

测试集的「标准证据」不是随手编的：按每道题对应条款里的关键句，去 MySQL 子块里
反查真正的 chunk_id，作为 recall@k / MRR 的标准答案。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.database import SessionLocal
from app.models import DocumentChunk

API = "http://127.0.0.1:8002/api"
DATASET_NAME = "教务政策评估集 V1"

CASES = [
    {
        "question": "大二学生可以申请转专业吗？",
        "reference_answer": "可以。具有本校全日制本科学籍的一年级、二年级在校生，已修课程全部合格、无未解除处分，且身体条件符合拟转入专业要求即可申请。",
        "gold": "具有本校全日制本科学籍的一年级或二年级在校学生",
        "type": "direct",
        "should_refuse": False,
    },
    {
        "question": "转专业每年什么时候申请？流程是怎样的？",
        "reference_answer": "每年 4 月 1 日至 4 月 15 日在教务系统提交申请，5 月 1 日至 5 月 20 日接收学院组织考核，5 月 25 日前公示 5 个工作日，7 月 10 日前完成学籍变更。",
        "gold": "4 月 1 日至 4 月 15 日",
        "type": "multi_hop",
        "should_refuse": False,
    },
    {
        "question": "补考和重修有什么区别？重修要交钱吗？",
        "reference_answer": "补考安排在下学期开学初，成绩达 60 分按 60 分记载并标注补考；补考仍不及格须重修，重修按学分缴纳学费，每学分 80 元，成绩按实际得分记载。",
        "gold": "每学分 80 元",
        "type": "direct",
        "should_refuse": False,
    },
    {
        "question": "国家奖学金的金额是多少？",
        "reference_answer": "国家奖学金每生每年 8000 元，国家励志奖学金每生每年 5000 元。",
        "gold": "国家奖学金奖励标准为每生每年 8000 元",
        "type": "exact_fact",
        "should_refuse": False,
    },
    {
        "question": "毕业论文文字复制比超过多少要延期答辩？",
        "reference_answer": "文字复制比高于 40% 的延期答辩，延期时间不少于半年；20% 至 40% 之间的须修改后复检。",
        "gold": "高于 40% 的，延期答辩",
        "type": "exact_fact",
        "should_refuse": False,
    },
    {
        "question": "拿学士学位对平均学分绩点有什么要求？",
        "reference_answer": "平均学分绩点不低于 2.0，且毕业论文（设计）成绩不低于 70 分。",
        "gold": "平均学分绩点不低于 2.0",
        "type": "direct",
        "should_refuse": False,
    },
    {
        "question": "学校第三食堂周末几点开门？",
        "reference_answer": "",
        "gold": None,
        "type": "out_of_scope",
        "should_refuse": True,
    },
]

RUNS = [
    ("仅向量检索", "vector"),
    ("混合检索（向量 + BM25）", "hybrid"),
    ("混合检索 + 重排序", "hybrid_rerank"),
    ("完整证据约束（+阈值过滤）", "full"),
]


def gold_chunk_ids(phrase: str) -> list[str]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.is_parent.is_(False))
            .where(DocumentChunk.content.contains(phrase))
        ).all()
        return [row.id for row in rows]


def main() -> None:
    with httpx.Client(timeout=60) as client:
        cases = []
        for case in CASES:
            ids = gold_chunk_ids(case["gold"]) if case["gold"] else []
            if case["gold"] and not ids:
                raise SystemExit(f"找不到标准证据：{case['gold']}")
            cases.append(
                {
                    "question": case["question"],
                    "reference_answer": case["reference_answer"],
                    "expected_chunk_ids": ids,
                    "question_type": case["type"],
                    "should_refuse": case["should_refuse"],
                }
            )

        dataset = client.post(
            f"{API}/evaluation/datasets",
            json={"name": DATASET_NAME, "description": "学籍 / 考核 / 奖助 / 学位四类条款", "cases": cases},
        )
        dataset.raise_for_status()
        dataset_id = dataset.json()["id"]
        print(f"测试集已创建：{DATASET_NAME}（{len(cases)} 题）")

        for name, mode in RUNS:
            run = client.post(
                f"{API}/evaluation/runs",
                json={
                    "dataset_id": dataset_id,
                    "name": name,
                    "mode": mode,
                    "top_k": 8,
                    "rerank_top_k": 4,
                    "min_evidence_score": 0.25,
                    "enable_judge": False,
                },
            )
            run.raise_for_status()
            run_id = run.json()["id"]
            while True:
                detail = client.get(f"{API}/evaluation/runs/{run_id}").json()
                if detail["status"] in {"completed", "failed"}:
                    break
                time.sleep(3)
            metrics = detail.get("metrics") or {}
            print(
                f"{name}：{detail['status']}　Recall@8={metrics.get('recall_at_k')}　"
                f"MRR={metrics.get('mrr')}　引用准确率={metrics.get('citation_precision')}　"
                f"幻觉率={metrics.get('hallucination_rate')}"
            )


if __name__ == "__main__":
    main()
