# tags 是将来显示在swagger 界面中让用户查看的
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from app.database import get_session
from app.models import PolicyDocument
from app.schemas import DocumentOut

from app.services.document_service import ingest_upload, delete_document, rebuild_index

router = APIRouter(prefix="/documents", tags=["documents"])

#/api/documents  一定要是post 请求才可以
@router.post("", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    topic: str | None = Form(default=None),
    effective_date: date | None = Form(default=None),
    session: Session = Depends(get_session),
):
	# 需要调用一个方法，这个方法可以真正实现file的上传，并返回一个DocumentOut对象
	try:
		print("上传文件开始")
		#return await save_upload(session, file, topic, effective_date)
		return await ingest_upload(session, file, topic, effective_date)
	except Exception as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=List[DocumentOut])
async def list_document(
    session: Session = Depends(get_session),
):
	return list(
		(
			session.scalars(
				select(PolicyDocument).order_by(PolicyDocument.created_at.desc())
			)
		).all()
	)

	# #或者是
	# #查询数据库中的所有文档
	# return session.query(PolicyDocument).order_by(PolicyDocument.created_at.desc()).all()

@router.delete("/{document_id}", status_code=204)
async def remove_document(
		document_id:str,session:Session = Depends(get_session)
):
	document=session.get(PolicyDocument,document_id)
	if not document:
		raise HTTPException(status_code=404, detail="文档不存在")
	await delete_document(session,document)


@router.post("/rebuild")
async def rebuild(session: Session = Depends(get_session)):
    count = await rebuild_index(session)
    return {"indexed_chunks": count}
