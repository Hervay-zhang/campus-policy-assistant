import asyncio
import csv
import io
import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.params import Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.database import get_session
from app.models import EvaluationCase, EvaluationDataset, EvaluationResult, EvaluationRun
from app.schemas import DatasetCreate, RunCreate, ManualScoreIn
from app.services.evaluation_service import execute_evaluation_run

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/datasets",summary="查询数据集以及每个数据中包含用例数")
async def list_datasets(session: Session = Depends(get_session)):
	count_query = (
		select(EvaluationCase.dataset_id, func.count(EvaluationCase.id).label("count"))
		.group_by(EvaluationCase.dataset_id)
		.subquery()
	)

	rows = (
		session.execute(
			select(EvaluationDataset, func.coalesce(count_query.c.count, 0))
			.outerjoin(count_query, count_query.c.dataset_id == EvaluationDataset.id)
			.order_by(EvaluationDataset.created_at.desc())
		)
	).all()

	return [
		{
			"id": dataset.id,
			"name": dataset.name,
			"description": dataset.description,
			"case_count": count,
			"created_at": dataset.created_at,
		}
		for dataset, count in rows
	]


@router.get("/runs",summary="查看评估运行情况")
async def list_runs(session: Session = Depends(get_session)):
	runs=session.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).all()
	runs_list=[]
	for row in runs:
		runs_list.append({
			"id": row.id,
			"name": row.name,
			"dataset_id": row.dataset_id,
			"status": row.status,
			"metrics": row.metrics,
			"rag_config": row.rag_config,
			"created_at": row.created_at,
		})

	return runs_list


# 保存数据集以及用例  这个函数会被复用
async def _create_dataset(session, payload):
	# 编写真正保存的代码
	evaluationDataset=EvaluationDataset(
		name=payload.name,
		description=payload.description)

	session.add(evaluationDataset)
	session.flush()
	dataset_id= evaluationDataset.id
	for case in payload.cases:
		session.add(
			EvaluationCase(
				dataset_id=dataset_id,
				question=case.question,
				reference_answer=case.reference_answer,
				expected_chunk_ids=case.expected_chunk_ids,
				question_type=case.question_type,
				should_refuse=case.should_refuse,
				metadata_json=case.metadata,
			)
		)

	session.commit()

	return {"id": dataset_id, "name": payload.name, "case_count": len(payload.cases)}



@router.post("/datasets",summary="保存数据集")
async def save_dataset(payload: DatasetCreate,session: Session = Depends(get_session)):
	return await _create_dataset(session, payload)



@router.post("/runs")
async def start_run(payload: RunCreate, session: Session = Depends(get_session)):
	# 先保存run
	# 判断数据集是否存在
	dataset_id=payload.dataset_id
	dataset=session.get(EvaluationDataset,dataset_id)
	if not dataset:
		raise HTTPException(status_code=404, detail="测试集不存在")

	# 保存run对象
	run=EvaluationRun(
		dataset_id=dataset_id,
		name=payload.name,
		# rag_config 的意思是本次运行时，页面上选择的一些配置参数
		rag_config=payload.model_dump(exclude={"dataset_id", "name"})
	)
	session.add(run)
	session.flush()
	run_id=run.id
	session.commit()

	# 真正执行 评估 的代码
	# create_task 是“ fire-and-forget ”，任务内部抛异常没人捕获，这里挂一个回调把异常打印出来
	task=asyncio.create_task(execute_evaluation_run(run_id))
	task.add_done_callback(lambda t: t.exception() and print(f"[evaluation] run {run_id} 执行失败: {t.exception()}"))
	return {"id": run.id, "status": run.status}


# 查询单个评估任务的详情（前端“历史运行”点击后展示指标用）
@router.get("/runs/{run_id}",summary="查询单个评估运行详情")
async def get_run(run_id:str, session: Session = Depends(get_session)):
	run=session.get(EvaluationRun,run_id)
	if not run:
		raise HTTPException(status_code=404, detail="评估任务不存在")
	return {
		"id": run.id,
		"name": run.name,
		"dataset_id": run.dataset_id,
		"status": run.status,
		"metrics": run.metrics,
		"rag_config": run.rag_config,
		"error_message": run.error_message,
		"started_at": run.started_at,
		"completed_at": run.completed_at,
		"created_at": run.created_at,
	}


# 查询某个评估任务下所有题目的逐题结果（前端“逐题诊断”用）
@router.get("/runs/{run_id}/cases",summary="查询评估运行的逐题结果")
async def get_run_cases(run_id:str, session: Session = Depends(get_session)):
	rows=(
		session.execute(
			select(EvaluationResult,EvaluationCase)
			.join(EvaluationCase,EvaluationResult.case_id==EvaluationCase.id)
			.where(EvaluationResult.run_id==run_id)
			.order_by(EvaluationResult.created_at)
		)
	).all()
	return [
		{
			"id": result.id,
			"question": case.question,
			"reference_answer": case.reference_answer,
			"answer": result.answer,
			"refused": result.refused,
			"latency_ms": result.latency_ms,
			"metrics": result.metrics,
			"trace": result.trace,
			"manual_score": result.manual_score or {},
		}
		for result,case in rows
	]


# 保存教师人工复核分数
@router.put("/results/{result_id}/manual-score",summary="保存人工复核分数")
async def save_manual_score(
	result_id:str,
	payload: ManualScoreIn,
	session: Session = Depends(get_session),
):
	result=session.get(EvaluationResult,result_id)
	if not result:
		raise HTTPException(status_code=404, detail="评估结果不存在")
	# 在原有分数基础上合并更新，避免未提交的字段被清空
	score=dict(result.manual_score or {})
	score.update(payload.model_dump(exclude_unset=True))
	result.manual_score=score
	session.commit()
	return {"id": result.id, "manual_score": score}


# 导出评估报告 CSV
@router.get("/runs/{run_id}/report",summary="导出评估报告CSV")
async def export_run_report(run_id:str, format:str="csv", session: Session = Depends(get_session)):
	run=session.get(EvaluationRun,run_id)
	if not run:
		raise HTTPException(status_code=404, detail="评估任务不存在")
	rows=(
		session.execute(
			select(EvaluationResult,EvaluationCase)
			.join(EvaluationCase,EvaluationResult.case_id==EvaluationCase.id)
			.where(EvaluationResult.run_id==run_id)
			.order_by(EvaluationResult.created_at)
		)
	).all()

	# 用 csv 模块写入内存字符串，再按 UTF-8 BOM 输出，保证 Excel 打开中文不乱码
	buffer=io.StringIO()
	writer=csv.writer(buffer)
	writer.writerow([
		"run_name","mode","question","reference_answer","answer","refused",
		"latency_ms","recall_at_k","mrr","citation_precision","refusal_accuracy",
		"factual_accuracy","hallucination_rate","faithfulness","relevance",
	])
	for result,case in rows:
		metrics=result.metrics or {}
		judge=result.judge_score or {}
		writer.writerow([
			run.name,
			(run.rag_config or {}).get("mode",""),
			case.question,
			case.reference_answer,
			result.answer,
			"是" if result.refused else "否",
			result.latency_ms,
			metrics.get("recall_at_k",""),
			metrics.get("mrr",""),
			metrics.get("citation_precision",""),
			metrics.get("refusal_accuracy",""),
			metrics.get("factual_accuracy",""),
			metrics.get("hallucination_rate",""),
			judge.get("faithfulness",""),
			judge.get("relevance",""),
		])

	filename=f"evaluation_{run.name}.csv"
	return StreamingResponse(
		iter(["\ufeff"+buffer.getvalue()]),
		media_type="text/csv; charset=utf-8",
		headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
	)


# 导入 CSV / JSONL 批量创建测试集
@router.post("/datasets/import",summary="导入CSV/JSONL测试集")
async def import_dataset(file: UploadFile = File(...), session: Session = Depends(get_session)):
	raw=(await file.read()).decode("utf-8-sig")
	filename=file.filename or "导入测试集"
	stem=filename.rsplit(".",1)[0] or filename
	lower=filename.lower()

	cases_data:list[dict]=[]
	if lower.endswith(".jsonl") or lower.endswith(".json"):
		for line in raw.splitlines():
			line=line.strip()
			if not line:
				continue
			try:
				obj=json.loads(line)
			except json.JSONDecodeError:
				continue
			if isinstance(obj,dict) and obj.get("question"):
				cases_data.append(obj)
	elif lower.endswith(".csv"):
		reader=csv.DictReader(io.StringIO(raw))
		for row in reader:
			question=(row.get("question") or "").strip()
			if not question:
				continue
			expected=[x.strip() for x in (row.get("expected_chunk_ids") or "").split(",") if x.strip()]
			cases_data.append({
				"question": question,
				"reference_answer": (row.get("reference_answer") or "").strip(),
				"question_type": (row.get("question_type") or "direct").strip(),
				"should_refuse": str(row.get("should_refuse") or "").strip().lower() in ("1","true","yes","是"),
				"expected_chunk_ids": expected,
			})
	else:
		raise HTTPException(status_code=400, detail="仅支持 CSV 或 JSONL 文件")

	if not cases_data:
		raise HTTPException(status_code=400, detail="文件中没有解析到有效的测试用例")

	# 测试集名称默认取文件名，重名时自动加序号
	name=stem
	exists=session.query(EvaluationDataset).filter(EvaluationDataset.name==name).first()
	if exists:
		suffix=2
		while session.query(EvaluationDataset).filter(EvaluationDataset.name==f"{name}({suffix})").first():
			suffix+=1
		name=f"{name}({suffix})"

	dataset=EvaluationDataset(name=name, description=f"从文件 {filename} 导入")
	session.add(dataset)
	session.flush()
	for item in cases_data:
		session.add(EvaluationCase(
			dataset_id=dataset.id,
			question=item["question"],
			reference_answer=item.get("reference_answer") or "",
			expected_chunk_ids=item.get("expected_chunk_ids") or [],
			question_type=item.get("question_type") or "direct",
			should_refuse=bool(item.get("should_refuse")),
			metadata_json=item.get("metadata") or {},
		))
	session.commit()
	return {"id": dataset.id, "name": dataset.name, "case_count": len(cases_data)}
