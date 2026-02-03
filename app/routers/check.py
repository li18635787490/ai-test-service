"""
API 路由 - 检测任务
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models import CheckDimension, TaskResponse, TaskStatus
from app.services.check_service import CheckService
from app.services.document_parser import DocumentParser
from app.routers.documents import get_document_path, get_document_info

router = APIRouter(prefix="/check", tags=["文档检测"])


class StartCheckRequest(BaseModel):
    """启动检测请求"""
    document_id: str = Field(..., description="文档 ID")
    dimensions: List[CheckDimension] = Field(
        default=[CheckDimension.FORMAT, CheckDimension.CONTENT],
        description="检测维度"
    )
    ai_provider: Optional[str] = Field(
        default=None,
        description="AI 提供商: openai / anthropic / qwen"
    )
    custom_rules: Optional[str] = Field(
        default=None,
        description="自定义检测规则"
    )


class StartCheckResponse(BaseModel):
    """启动检测响应"""
    task_id: str
    message: str


@router.post("/start", response_model=StartCheckResponse)
async def start_check(request: StartCheckRequest):
    """
    启动文档检测任务

    - **document_id**: 上传文档后获得的文档 ID
    - **dimensions**: 检测维度列表
        - format: 格式规范检测
        - content: 内容质量检测
        - logic: 逻辑一致性检测
        - sensitive: 敏感信息检测
        - compliance: 合规性检测
    - **ai_provider**: AI 提供商 (openai/anthropic/qwen)
    - **custom_rules**: 自定义检测规则描述
    """
    # 获取文档
    doc_path = get_document_path(request.document_id)
    doc_info = get_document_info(request.document_id)

    # 解析文档内容
    try:
        content, _ = await DocumentParser.parse(doc_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文档解析失败: {str(e)}")

    # 创建检测任务
    service = CheckService()
    task_id = await service.create_task(
        document=doc_info,
        content=content,
        dimensions=request.dimensions,
        ai_provider_name=request.ai_provider,
        custom_rules=request.custom_rules
    )

    return StartCheckResponse(
        task_id=task_id,
        message="检测任务已创建，正在处理中"
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """
    查询检测任务状态

    返回任务当前状态、进度和检测结果
    """
    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_id}/wait", response_model=TaskResponse)
async def wait_for_completion(task_id: str, timeout: int = 60):
    """
    等待任务完成（轮询）

    - **timeout**: 最大等待时间（秒）
    """
    import asyncio

    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    elapsed = 0
    while task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING) and elapsed < timeout:
        await asyncio.sleep(1)
        elapsed += 1
        task = CheckService.get_task(task_id)

    return task
