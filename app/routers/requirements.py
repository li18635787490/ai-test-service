"""
API 路由 - 需求分析与测试用例生成
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.models import RequirementAnalysisResult, TestCaseGenerationResult
from app.services.requirement_analyzer import RequirementAnalyzer
from app.services.document_parser import DocumentParser
from app.routers.documents import get_document_path, get_document_info

router = APIRouter(prefix="/requirements", tags=["需求分析"])


class AnalyzeRequest(BaseModel):
    """需求分析请求"""
    document_id: str = Field(..., description="文档 ID")
    ai_provider: Optional[str] = Field(default=None, description="AI 提供商")


class GenerateTestCasesRequest(BaseModel):
    """生成测试用例请求"""
    document_id: str = Field(..., description="文档 ID")
    ai_provider: Optional[str] = Field(default=None, description="AI 提供商")


@router.post("/analyze", response_model=RequirementAnalysisResult)
async def analyze_requirements(request: AnalyzeRequest):
    """
    分析需求文档

    对需求文档进行全面分析，包括：
    - 需求完整性检查
    - 场景覆盖检查
    - 描述质量检查
    - 可测试性检查

    返回详细的分析报告和改进建议。
    """
    try:
        # 获取文档内容
        doc_path = get_document_path(request.document_id)
        content, _ = await DocumentParser.parse(doc_path)

        # 分析需求
        analyzer = RequirementAnalyzer(request.ai_provider)
        result = await analyzer.analyze_requirements(content)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求分析失败: {str(e)}")


@router.post("/generate-testcases", response_model=TestCaseGenerationResult)
async def generate_test_cases(request: GenerateTestCasesRequest):
    """
    根据需求文档生成测试用例

    自动生成功能测试用例，包括：
    - 正向测试用例
    - 反向测试用例
    - 边界测试用例
    - 异常测试用例

    每个用例包含详细的测试步骤和预期结果。
    """
    try:
        # 获取文档内容
        doc_path = get_document_path(request.document_id)
        content, _ = await DocumentParser.parse(doc_path)

        # 生成测试用例
        analyzer = RequirementAnalyzer(request.ai_provider)
        result = await analyzer.generate_test_cases(content, request.document_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试用例生成失败: {str(e)}")


@router.get("/generate-testcases/export")
async def export_test_cases(document_id: str, format: str = "markdown", ai_provider: Optional[str] = None):
    """
    生成并导出测试用例

    - **document_id**: 文档 ID
    - **format**: 导出格式 (markdown / csv / json)
    - **ai_provider**: AI 提供商
    """
    try:
        # 获取文档内容
        doc_path = get_document_path(document_id)
        doc_info = get_document_info(document_id)
        content, _ = await DocumentParser.parse(doc_path)

        # 生成测试用例
        analyzer = RequirementAnalyzer(ai_provider)
        result = await analyzer.generate_test_cases(content, document_id)

        if format == "markdown":
            output = _export_markdown(result, doc_info.filename)
            return PlainTextResponse(content=output, media_type="text/markdown")
        elif format == "csv":
            output = _export_csv(result)
            return PlainTextResponse(content=output, media_type="text/csv")
        else:
            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _export_markdown(result: TestCaseGenerationResult, filename: str) -> str:
    """导出为 Markdown 格式"""
    lines = [
        f"# 测试用例文档",
        f"",
        f"**源文档**: {filename}",
        f"**生成时间**: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**用例总数**: {result.total_cases}",
        f"",
        f"## 覆盖情况",
        f"",
        f"{result.coverage_summary}",
        f"",
        f"---",
        f"",
        f"## 测试用例列表",
        f""
    ]

    for tc in result.test_cases:
        priority_emoji = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🟢"}
        emoji = priority_emoji.get(tc.priority.value, "⚪")

        lines.append(f"### {tc.case_id}: {tc.title}")
        lines.append(f"")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| **优先级** | {emoji} {tc.priority.value} |")
        lines.append(f"| **类型** | {tc.case_type.value} |")
        if tc.requirement_id:
            lines.append(f"| **关联需求** | {tc.requirement_id} |")
        if tc.precondition:
            lines.append(f"| **前置条件** | {tc.precondition} |")
        if tc.test_data:
            lines.append(f"| **测试数据** | {tc.test_data} |")
        if tc.tags:
            lines.append(f"| **标签** | {', '.join(tc.tags)} |")

        lines.append(f"")
        lines.append(f"**测试步骤:**")
        lines.append(f"")
        lines.append(f"| 步骤 | 操作 | 预期结果 |")
        lines.append(f"|------|------|----------|")

        for step in tc.steps:
            lines.append(f"| {step.step_number} | {step.action} | {step.expected_result} |")

        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    return "\n".join(lines)


def _export_csv(result: TestCaseGenerationResult) -> str:
    """导出为 CSV 格式"""
    lines = ["用例编号,标题,优先级,类型,关联需求,前置条件,测试步骤,预期结果,测试数据,标签"]

    for tc in result.test_cases:
        steps_str = "; ".join([f"{s.step_number}. {s.action}" for s in tc.steps])
        expected_str = "; ".join([f"{s.step_number}. {s.expected_result}" for s in tc.steps])
        tags_str = "|".join(tc.tags)

        line = f'"{tc.case_id}","{tc.title}","{tc.priority.value}","{tc.case_type.value}",'
        line += f'"{tc.requirement_id or ""}","{tc.precondition or ""}",'
        line += f'"{steps_str}","{expected_str}","{tc.test_data or ""}","{tags_str}"'
        lines.append(line)

    return "\n".join(lines)


# ============ 需求分析结果导出 ============

@router.get("/analyze/export")
async def export_analysis(document_id: str, format: str = "markdown", ai_provider: Optional[str] = None):
    """
    导出需求分析结果

    - **document_id**: 文档 ID
    - **format**: 导出格式 (markdown / json)
    - **ai_provider**: AI 提供商
    """
    try:
        # 获取文档内容
        doc_path = get_document_path(document_id)
        doc_info = get_document_info(document_id)
        content, _ = await DocumentParser.parse(doc_path)

        # 分析需求
        analyzer = RequirementAnalyzer(ai_provider)
        result = await analyzer.analyze_requirements(content)

        if format == "markdown":
            output = _export_analysis_markdown(result, doc_info.filename)
            return PlainTextResponse(content=output, media_type="text/markdown")
        else:
            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


def _export_analysis_markdown(result: RequirementAnalysisResult, filename: str) -> str:
    """导出需求分析结果为 Markdown 格式"""
    from datetime import datetime

    # 评分颜色函数
    def get_score_emoji(score):
        if score >= 80:
            return "🟢"
        elif score >= 60:
            return "🟡"
        else:
            return "🔴"

    lines = [
        f"# 📋 需求分析报告",
        f"",
        f"| 项目 | 信息 |",
        f"|------|------|",
        f"| **源文档** | {filename} |",
        f"| **分析时间** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| **需求总数** | {result.total_requirements} 个功能点 |",
        f"",
        f"---",
        f"",
        f"## 📊 评分总览",
        f"",
        f"| 维度 | 得分 | 状态 |",
        f"|------|:----:|:----:|",
        f"| 🎯 完整性 | {result.completeness_score} | {get_score_emoji(result.completeness_score)} |",
        f"| 📋 场景覆盖 | {result.scenario_coverage_score} | {get_score_emoji(result.scenario_coverage_score)} |",
        f"| 📝 描述质量 | {result.description_quality_score} | {get_score_emoji(result.description_quality_score)} |",
        f"| ✅ 可测试性 | {result.testability_score} | {get_score_emoji(result.testability_score)} |",
        f"| **🏆 综合得分** | **{result.overall_score}** | {get_score_emoji(result.overall_score)} |",
        f"",
        f"---",
        f"",
        f"## 📝 分析总结",
        f"",
        f"> {result.summary}",
        f"",
        f"---",
        f"",
        f"## 🔍 需求详细分析",
        f""
    ]

    for idx, req in enumerate(result.analyzed_requirements, 1):
        issue_count = len(req.issues)
        status = f"❌ {issue_count} 个问题" if issue_count > 0 else "✅ 完整"

        lines.append(f"### {idx}. {req.req_id}: {req.title}")
        lines.append(f"")
        lines.append(f"| 属性 | 值 |")
        lines.append(f"|------|------|")
        lines.append(f"| **优先级** | {req.priority or '未定义'} |")
        lines.append(f"| **状态** | {status} |")
        lines.append(f"")
        lines.append(f"**需求描述：**")
        lines.append(f"> {req.description}")
        lines.append(f"")

        if req.issues:
            lines.append(f"#### 🔴 发现的问题 ({len(req.issues)})")
            lines.append(f"")
            for issue in req.issues:
                # 解析问题类型
                import re
                match = re.match(r'^\[([^\]]+)\]\s*(.*)$', issue)
                if match:
                    lines.append(f"- **`{match.group(1)}`** {match.group(2)}")
                else:
                    lines.append(f"- {issue}")
            lines.append(f"")

        if req.suggestions:
            lines.append(f"#### 💡 改进建议 ({len(req.suggestions)})")
            lines.append(f"")
            for suggestion in req.suggestions:
                lines.append(f"- {suggestion}")
            lines.append(f"")

        lines.append(f"---")
        lines.append(f"")

    if result.improvement_suggestions:
        lines.append(f"## 📌 整体改进建议")
        lines.append(f"")
        for idx, suggestion in enumerate(result.improvement_suggestions, 1):
            # 解析优先级
            import re
            match = re.match(r'^\[([^\]]+)\]\s*(.*)$', suggestion)
            if match:
                priority = match.group(1)
                content = match.group(2)
                emoji = "🔴" if "高" in priority else "🟡" if "中" in priority else "🟢"
                lines.append(f"{idx}. {emoji} **{priority}** - {content}")
            else:
                lines.append(f"{idx}. {suggestion}")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*报告由 AI 文档检测服务自动生成*")

    return "\n".join(lines)

