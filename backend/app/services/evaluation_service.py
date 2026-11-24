import json
import re
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.database import SessionLocal
from app.models import EvaluationRun, RunStatus, EvaluationCase, EvaluationResult
from app.schemas import RetrievalFilters
from app.services.metrics import recall_at_k, reciprocal_rank, citation_precision, factual_accuracy, citation_coverage
from app.services.model_factory import create_chat_model, invoke_text
from app.services.rag_service import answer_question

def aggregate_metrics(results: list[EvaluationResult]) -> dict[str, float | int]:
    if not results:
        return {"case_count": 0}
    metric_names = [
        "recall_at_k",
        "mrr",
        "citation_precision",
        "refusal_accuracy",
        "factual_accuracy",
        "faithfulness",
        "relevance",
        "hallucination_rate",
    ]
    aggregate: dict[str, float | int] = {"case_count": len(results)}
    for name in metric_names:
        values = [
            float(result.metrics[name])
            for result in results
            if name in result.metrics and result.metrics[name] is not None
        ]
        # 没跑的指标（例如未启用 LLM Judge 时的忠实度/相关性）不写入，前端也就不会显示成 0%
        if values:
            aggregate[name] = round(sum(values) / len(values), 4)
    aggregate["average_latency_ms"] = round(
        sum(result.latency_ms for result in results) / len(results), 2
    )
    return aggregate


async def judge_answer(
    question: str, reference: str, answer: str, context: str
) -> dict[str, Any]:
    # 编写提示词
    prompt = f"""你是独立的 RAG 评估器。只输出 JSON：
    {{"faithfulness":0到1,"relevance":0到1,"factual_accuracy":0到1,
    "hallucination_rate":0到1,"reason":"简短理由"}}
    忠实度仅判断答案是否由上下文支持。
    问题：{question}
    参考答案：{reference}
    上下文：{context}
    待评答案：{answer}
    """
    try:
        llm=create_chat_model(get_settings(),temperature=0)
        output, _=await invoke_text(llm,prompt)
        print(output)
        # 从output中获取 json部分的数据
        match = re.search(r"\{.*\}", output, re.S)
        return json.loads(match.group(0)) if match else {}
    except Exception as e:
        return {"error":str(e)}


async def execute_evaluation_run(run_id):
    # 将run的状态修改为runnning
    with SessionLocal() as session:
        run:EvaluationRun=session.get(EvaluationRun,run_id)
        if not run:
            return
        try:
            run.status = RunStatus.running
            run.started_at = datetime.now(timezone.utc)
            session.commit()
            cases=session.query(EvaluationCase).filter(EvaluationCase.dataset_id==run.dataset_id).all()
            config = run.rag_config
            stored_results: list[EvaluationResult] = []
            llm_judge=config.get("enable_judge",False)
            top_k=config.get("top_k", 8)

            for case in cases:
                # 通过循环去进行ask
                ragAnswer=await answer_question(
                    session,
                    case.question,
                    RetrievalFilters(),
                    mode=config["mode"],
                    top_k=top_k,
                    rerank_top_k=config["rerank_top_k"],
                    min_score=config["min_evidence_score"],
                )

                expected_list=case.expected_chunk_ids or []
                trace=ragAnswer.trace
                final_evidence=trace.get("final_evidence", [])
                retrieved_list=[evidence.get("chunk_id") for evidence in final_evidence]

                citations=ragAnswer.citations
                citation_list=[item.get("chunk_id") for item in citations]

                # 通过五个指标对answer进行体检
                # 计算幻觉率
                if ragAnswer.refused:
                    hallucination_rate=0.0
                else:
                    hallucination_rate= 1 - citation_coverage(ragAnswer.answer)

                # 指标计算结果
                metrics={
                    "recall_at_k":recall_at_k(expected_list,retrieved_list,top_k),
                    "mrr":reciprocal_rank(expected_list,retrieved_list),
                    "citation_precision": citation_precision(citation_list, retrieved_list),
                    "refusal_accuracy": float(ragAnswer.refused == case.should_refuse),
                    "factual_accuracy": factual_accuracy(
                        case.reference_answer, ragAnswer.answer
                    ),
                    # 幻觉率
                    "hallucination_rate": hallucination_rate
                }

                context="\n".join([item['content'] for item in final_evidence])

                if llm_judge:
                    judge_score=await judge_answer(
                        case.question,
                        case.reference_answer,
                        ragAnswer.answer,
                        context
                    )
                else:
                    judge_score=dict()

                result = EvaluationResult(
                    run_id=run.id,
                    case_id=case.id,
                    answer=ragAnswer.answer,
                    refused=ragAnswer.refused,
                    retrieved_chunk_ids=retrieved_list,
                    cited_chunk_ids=citation_list,
                    metrics=metrics,
                    trace=trace,
                    judge_score=judge_score,
                    latency_ms=ragAnswer.latency_ms,
                    token_usage=ragAnswer.token_usage,
                )
                session.add(result)
                stored_results.append(result)
                # 逐题落库：长测试集中途被打断也能保留已跑完的结果
                session.commit()

            run.metrics = aggregate_metrics(stored_results)
            run.status = RunStatus.completed
            run.error_message = None
            run.completed_at = datetime.now(timezone.utc)
            session.commit()
        except Exception as exc:
            # 评估任务失败时，把 run 标记为 failed，避免永远卡在 running 状态
            session.rollback()
            run.status = RunStatus.failed
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            session.commit()