"""
报告生成服务
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from app.config import get_settings
from app.models import TaskResponse, ReportResponse, Severity


class ReportGenerator:
    """报告生成器"""

    def __init__(self):
        self.settings = get_settings()
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def generate_report_data(self, task: TaskResponse) -> ReportResponse:
        """生成报告数据"""
        if not task.results:
            raise ValueError("任务尚未完成检测")

        # 统计问题数量
        error_count = 0
        warning_count = 0
        info_count = 0

        for result in task.results:
            for issue in result.issues:
                if issue.severity == Severity.ERROR:
                    error_count += 1
                elif issue.severity == Severity.WARNING:
                    warning_count += 1
                else:
                    info_count += 1

        return ReportResponse(
            task_id=task.task_id,
            document=task.document,
            overall_score=task.overall_score or 0,
            summary=task.summary or "",
            results=task.results,
            total_issues=error_count + warning_count + info_count,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            generated_at=datetime.now()
        )

    def render_html(self, report: ReportResponse) -> str:
        """渲染 HTML 报告"""
        template = self.env.get_template("report.html")
        return template.render(report=report)

    def render_markdown(self, report: ReportResponse) -> str:
        """渲染 Markdown 报告"""
        lines = [
            f"# 文档检测报告",
            f"",
            f"## 基本信息",
            f"- **文档名称**: {report.document.filename}",
            f"- **文件类型**: {report.document.file_type.value.upper()}",
            f"- **检测时间**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 整体评估",
            f"- **综合得分**: {report.overall_score} / 100",
            f"- **问题总数**: {report.total_issues} (错误: {report.error_count}, 警告: {report.warning_count}, 提示: {report.info_count})",
            f"",
            f"### 总结",
            f"{report.summary}",
            f"",
            f"---",
            f"",
            f"## 详细检测结果",
        ]

        for result in report.results:
            lines.append(f"")
            lines.append(f"### {result.dimension.value.upper()} 检测")
            lines.append(f"- **得分**: {result.score}")
            lines.append(f"- **总结**: {result.summary}")

            if result.issues:
                lines.append(f"")
                lines.append(f"#### 发现的问题")
                for i, issue in enumerate(result.issues, 1):
                    severity_emoji = {"error": "🔴", "warning": "🟡", "info": "🔵"}
                    emoji = severity_emoji.get(issue.severity.value, "⚪")
                    lines.append(f"")
                    lines.append(f"**{i}. {emoji} [{issue.severity.value.upper()}]** {issue.description}")
                    if issue.location:
                        lines.append(f"   - 位置: {issue.location}")
                    if issue.suggestion:
                        lines.append(f"   - 建议: {issue.suggestion}")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"*报告生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    async def save_report(
        self,
        report: ReportResponse,
        format: str = "html"
    ) -> str:
        """保存报告到文件"""
        os.makedirs(self.settings.report_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report.task_id[:8]}_{timestamp}.{format}"
        filepath = os.path.join(self.settings.report_dir, filename)

        if format == "html":
            content = self.render_html(report)
        elif format == "md":
            content = self.render_markdown(report)
        else:
            raise ValueError(f"不支持的报告格式: {format}")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
