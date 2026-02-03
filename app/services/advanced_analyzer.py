"""
高级需求分析服务 - 需求关联分析、冲突检测、重复检测、历史学习
"""
import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from app.config import get_settings
from app.services.ai_providers import get_ai_provider


class AdvancedRequirementAnalyzer:
    """高级需求分析器"""

    # 历史分析结果存储路径
    HISTORY_DIR = Path("analysis_history")

    def __init__(self, ai_provider_name: Optional[str] = None):
        self.ai_provider = get_ai_provider(ai_provider_name)
        self.HISTORY_DIR.mkdir(exist_ok=True)

    async def analyze_dependencies(self, requirements: List[Dict]) -> Dict:
        """分析需求之间的依赖关系"""

        req_summary = "\n".join([
            f"- {r.get('req_id', f'REQ-{i+1}')}: {r.get('title', '')} - {r.get('description', '')[:100]}"
            for i, r in enumerate(requirements)
        ])

        prompt = """你是一个需求分析专家。请分析以下需求之间的依赖关系。

## 分析要点
1. **前置依赖**：哪些需求必须先完成才能开发其他需求
2. **数据依赖**：哪些需求共享相同的数据或业务实体
3. **功能依赖**：哪些需求的功能互相调用或依赖
4. **建议开发顺序**：基于依赖关系给出合理的开发优先级

## 输出格式（JSON）：
{
    "dependencies": [
        {
            "from_req": "REQ-001",
            "to_req": "REQ-002",
            "type": "前置依赖",
            "reason": "用户注册功能必须先完成，登录功能才能测试"
        }
    ],
    "dependency_graph": {
        "REQ-001": ["REQ-002", "REQ-003"],
        "REQ-002": ["REQ-004"]
    },
    "recommended_order": [
        {"phase": 1, "requirements": ["REQ-001"], "reason": "基础功能，无依赖"},
        {"phase": 2, "requirements": ["REQ-002", "REQ-003"], "reason": "依赖REQ-001"}
    ],
    "critical_path": ["REQ-001", "REQ-002", "REQ-005"],
    "summary": "共发现X个依赖关系，建议分X个阶段开发..."
}

只返回JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请分析以下需求的依赖关系：\n\n{req_summary}"}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            return self._parse_json(result_text)
        except Exception as e:
            return {"error": str(e), "dependencies": [], "summary": "依赖分析失败"}

    async def detect_conflicts(self, requirements: List[Dict]) -> Dict:
        """检测需求之间的冲突"""

        req_details = "\n\n".join([
            f"### {r.get('req_id', f'REQ-{i+1}')}: {r.get('title', '')}\n{r.get('description', '')}"
            for i, r in enumerate(requirements)
        ])

        prompt = """你是一个需求分析专家。请检测以下需求之间是否存在冲突。

## 冲突类型
1. **逻辑冲突**：两个需求的业务逻辑互相矛盾
2. **资源冲突**：两个需求对同一资源有不同的操作要求
3. **时序冲突**：两个需求对同一流程的时序要求不一致
4. **数据冲突**：两个需求对同一数据有不同的定义或处理方式
5. **规则冲突**：两个需求定义了矛盾的业务规则

## 输出格式（JSON）：
{
    "conflicts": [
        {
            "req_a": "REQ-001",
            "req_b": "REQ-003",
            "conflict_type": "逻辑冲突",
            "severity": "高",
            "description": "REQ-001要求订单取消后立即退款，REQ-003要求取消后48小时内退款",
            "suggestion": "建议统一退款时间规则，明确不同场景的退款时效"
        }
    ],
    "potential_risks": [
        {
            "requirements": ["REQ-002", "REQ-004"],
            "risk": "两个需求都涉及库存操作，可能存在并发风险",
            "suggestion": "建议明确库存操作的锁定机制"
        }
    ],
    "conflict_count": 2,
    "high_severity_count": 1,
    "summary": "发现X个冲突，其中X个高危冲突需要立即处理..."
}

只返回JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请检测以下需求之间的冲突：\n\n{req_details}"}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            return self._parse_json(result_text)
        except Exception as e:
            return {"error": str(e), "conflicts": [], "summary": "冲突检测失败"}

    async def detect_duplicates(self, requirements: List[Dict]) -> Dict:
        """检测重复或相似的需求"""

        req_details = "\n\n".join([
            f"### {r.get('req_id', f'REQ-{i+1}')}: {r.get('title', '')}\n{r.get('description', '')}"
            for i, r in enumerate(requirements)
        ])

        prompt = """你是一个需求分析专家。请检测以下需求中是否存在重复或高度相似的内容。

## 检测标准
1. **完全重复**：两个需求描述的是完全相同的功能
2. **功能重叠**：两个需求有大部分功能重叠
3. **部分重复**：两个需求有部分内容重复
4. **相似功能**：两个需求功能相似，可能可以合并

## 输出格式（JSON）：
{
    "duplicates": [
        {
            "req_a": "REQ-002",
            "req_b": "REQ-005",
            "similarity": 85,
            "duplicate_type": "功能重叠",
            "overlapping_parts": "两者都描述了用户密码修改功能",
            "suggestion": "建议合并为一个需求，统一密码修改的入口和流程"
        }
    ],
    "merge_suggestions": [
        {
            "requirements": ["REQ-002", "REQ-005"],
            "merged_title": "用户密码管理功能",
            "reason": "功能相似度高，合并后更易于维护"
        }
    ],
    "duplicate_count": 2,
    "summary": "发现X组重复/相似需求，建议合并X组..."
}

只返回JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请检测以下需求的重复情况：\n\n{req_details}"}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            return self._parse_json(result_text)
        except Exception as e:
            return {"error": str(e), "duplicates": [], "summary": "重复检测失败"}

    def save_analysis_history(self, project_id: str, analysis_result: Dict) -> str:
        """保存分析历史，用于后续学习"""
        history_file = self.HISTORY_DIR / f"{project_id}_history.json"

        # 加载现有历史
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        # 添加新记录
        record = {
            "id": hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            "timestamp": datetime.now().isoformat(),
            "analysis_result": analysis_result
        }
        history.append(record)

        # 只保留最近50条记录
        history = history[-50:]

        # 保存
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        return record["id"]

    def get_analysis_history(self, project_id: str) -> List[Dict]:
        """获取历史分析记录"""
        history_file = self.HISTORY_DIR / f"{project_id}_history.json"

        if not history_file.exists():
            return []

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    async def learn_from_history(self, project_id: str) -> Dict:
        """从历史分析中学习项目特点，生成分析建议"""
        history = self.get_analysis_history(project_id)

        if len(history) < 3:
            return {
                "has_learning": False,
                "message": "历史数据不足，至少需要3次分析记录才能生成学习报告",
                "suggestions": []
            }

        # 提取历史问题模式
        all_issues = []
        for record in history[-10:]:  # 最近10条
            result = record.get("analysis_result", {})
            for req in result.get("analyzed_requirements", []):
                all_issues.extend(req.get("issues", []))

        if not all_issues:
            return {
                "has_learning": False,
                "message": "历史记录中没有发现问题，无法生成学习报告",
                "suggestions": []
            }

        issues_text = "\n".join([f"- {issue}" for issue in all_issues[:50]])

        prompt = """你是一个需求质量顾问。基于以下历史分析中发现的问题，总结这个项目的常见问题模式，并给出针对性的建议。

## 任务
1. 识别重复出现的问题类型
2. 分析问题的根本原因
3. 给出针对性的改进建议
4. 为后续需求分析提供关注重点

## 输出格式（JSON）：
{
    "has_learning": true,
    "common_patterns": [
        {
            "pattern": "业务规则描述不完整",
            "frequency": "高",
            "examples": ["积分规则未说明", "退款规则不清晰"],
            "root_cause": "产品文档模板缺少业务规则章节"
        }
    ],
    "project_characteristics": [
        "电商类项目，涉及大量交易流程",
        "多角色系统（用户、商家、运营）"
    ],
    "improvement_suggestions": [
        "建议在需求模板中增加'业务规则'必填章节",
        "建议每个涉及金额的需求必须说明计算公式"
    ],
    "focus_points_for_next_analysis": [
        "重点关注逆向流程（退款、取消、退货）的完整性",
        "关注多角色场景下的权限定义"
    ],
    "summary": "该项目主要问题集中在..."
}

只返回JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"以下是历史分析中发现的问题：\n\n{issues_text}"}
                ],
                temperature=0.5
            )

            result_text = response.choices[0].message.content
            return self._parse_json(result_text)
        except Exception as e:
            return {
                "has_learning": False,
                "message": f"学习分析失败: {str(e)}",
                "suggestions": []
            }

    def _parse_json(self, text: str) -> Dict:
        """解析JSON文本"""
        text = text.strip()

        # 处理 markdown 代码块
        if "```" in text:
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if json_match:
                text = json_match.group(1).strip()

        # 找到JSON对象
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            text = text[start_idx:end_idx + 1]

        try:
            return json.loads(text)
        except:
            return {"error": "JSON解析失败", "raw": text[:500]}
