"""
检测服务 - 核心业务逻辑
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.models import (
    CheckDimension, CheckResult, TaskStatus, DocumentInfo,
    TaskResponse
)
from app.services.ai_providers import get_ai_provider, BaseAIProvider


# 简单的内存存储（生产环境应使用数据库）
_tasks: Dict[str, TaskResponse] = {}
_document_contents: Dict[str, str] = {}


class CheckService:
    """文档检测服务"""

    def __init__(self, ai_provider: Optional[BaseAIProvider] = None):
        self.ai_provider = ai_provider

    async def create_task(
        self,
        document: DocumentInfo,
        content: str,
        dimensions: List[CheckDimension],
        ai_provider_name: Optional[str] = None,
        custom_rules: Optional[str] = None
    ) -> str:
        """创建检测任务"""
        task_id = str(uuid.uuid4())

        task = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            document=document,
            progress=0,
            created_at=datetime.now()
        )

        _tasks[task_id] = task
        _document_contents[task_id] = content

        # 启动异步检测任务
        asyncio.create_task(
            self._run_check(task_id, content, dimensions, ai_provider_name, custom_rules)
        )

        return task_id

    async def _run_check(
        self,
        task_id: str,
        content: str,
        dimensions: List[CheckDimension],
        ai_provider_name: Optional[str] = None,
        custom_rules: Optional[str] = None
    ):
        """执行检测任务"""
        task = _tasks.get(task_id)
        if not task:
            return

        try:
            task.status = TaskStatus.PROCESSING

            # 获取 AI 提供商
            ai_provider = self.ai_provider or get_ai_provider(ai_provider_name)

            results: List[CheckResult] = []
            total_dimensions = len(dimensions)

            # 逐维度检测
            for i, dimension in enumerate(dimensions):
                result = await ai_provider.analyze(content, dimension, custom_rules)
                results.append(result)

                # 更新进度
                task.progress = int((i + 1) / total_dimensions * 90)

            # 生成整体总结
            summary = await ai_provider.generate_summary(content, results)

            # 计算整体得分
            overall_score = sum(r.score for r in results) / len(results) if results else 0

            # 更新任务结果
            task.results = results
            task.overall_score = round(overall_score, 1)
            task.summary = summary
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now()

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.summary = f"检测失败: {str(e)}"

    @staticmethod
    def get_task(task_id: str) -> Optional[TaskResponse]:
        """获取任务状态"""
        return _tasks.get(task_id)

    @staticmethod
    def get_task_content(task_id: str) -> Optional[str]:
        """获取任务对应的文档内容"""
        return _document_contents.get(task_id)

    @staticmethod
    def calculate_issue_counts(results: List[CheckResult]) -> Dict[str, int]:
        """统计问题数量"""
        counts = {"error": 0, "warning": 0, "info": 0, "total": 0}

        for result in results:
            for issue in result.issues:
                counts[issue.severity.value] += 1
                counts["total"] += 1

        return counts
