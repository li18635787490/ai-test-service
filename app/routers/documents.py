"""
API 路由 - 文档管理
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
import aiofiles

from app.config import get_settings
from app.models import DocumentInfo
from app.services.document_parser import DocumentParser

router = APIRouter(prefix="/documents", tags=["文档管理"])

# 简单的内存存储
_documents: dict = {}


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档

    支持格式: PDF, DOCX, XLSX, PPTX, TXT, MD
    """
    # 验证文件类型
    doc_type = DocumentParser.get_document_type(file.filename)
    if not doc_type:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: PDF, DOCX, XLSX, PPTX, TXT, MD"
        )

    # 生成文档 ID
    doc_id = str(uuid.uuid4())

    # 保存文件
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)

    ext = Path(file.filename).suffix
    save_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")

    # 异步保存文件
    content = await file.read()
    async with aiofiles.open(save_path, 'wb') as f:
        await f.write(content)

    # 解析获取页数
    try:
        _, page_count = await DocumentParser.parse(save_path)
    except Exception:
        page_count = None

    # 创建文档信息
    doc_info = DocumentInfo(
        id=doc_id,
        filename=file.filename,
        file_type=doc_type,
        file_size=len(content),
        page_count=page_count,
        upload_time=datetime.now()
    )

    _documents[doc_id] = {
        "info": doc_info,
        "path": save_path
    }

    return doc_info


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """获取文档信息"""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc["info"]


@router.get("/", response_model=List[DocumentInfo])
async def list_documents():
    """获取文档列表"""
    return [doc["info"] for doc in _documents.values()]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """删除文档"""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 删除文件
    if os.path.exists(doc["path"]):
        os.remove(doc["path"])

    del _documents[document_id]
    return {"message": "文档已删除"}


def get_document_path(document_id: str) -> str:
    """获取文档文件路径（内部使用）"""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc["path"]


def get_document_info(document_id: str) -> DocumentInfo:
    """获取文档信息（内部使用）"""
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc["info"]
