"""
API 路由 - 报告
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse

from app.models import ReportResponse, TaskStatus
from app.services.check_service import CheckService
from app.services.report_generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["检测报告"])


@router.get("/{task_id}", response_model=ReportResponse)
async def get_report(task_id: str):
    """
    获取检测报告数据

    返回 JSON 格式的完整报告数据
    """
    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    generator = ReportGenerator()
    return generator.generate_report_data(task)


@router.get("/{task_id}/html", response_class=HTMLResponse)
async def get_html_report(task_id: str):
    """
    获取 HTML 格式报告

    返回可直接在浏览器中查看的 HTML 报告
    """
    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    generator = ReportGenerator()
    report = generator.generate_report_data(task)
    html_content = generator.render_html(report)

    return HTMLResponse(content=html_content)


@router.get("/{task_id}/markdown", response_class=PlainTextResponse)
async def get_markdown_report(task_id: str):
    """
    获取 Markdown 格式报告
    """
    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    generator = ReportGenerator()
    report = generator.generate_report_data(task)
    md_content = generator.render_markdown(report)

    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown"
    )


@router.get("/{task_id}/download")
async def download_report(task_id: str, format: str = "html"):
    """
    下载报告文件

    - **format**: 报告格式 (html / md)
    """
    if format not in ("html", "md"):
        raise HTTPException(status_code=400, detail="不支持的格式，请使用 html 或 md")

    task = CheckService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )

    generator = ReportGenerator()
    report = generator.generate_report_data(task)
    filepath = await generator.save_report(report, format)

    return FileResponse(
        path=filepath,
        filename=f"report_{task_id[:8]}.{format}",
        media_type="application/octet-stream"
    )
