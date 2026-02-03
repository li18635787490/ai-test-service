"""
AI 提供商抽象层 - 支持多种 AI 服务的统一接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List
import json

from app.config import get_settings
from app.models import CheckDimension, CheckResult, Issue, Severity


class BaseAIProvider(ABC):
    """AI 提供商基类"""

    @abstractmethod
    async def analyze(
        self,
        content: str,
        dimension: CheckDimension,
        custom_rules: Optional[str] = None
    ) -> CheckResult:
        """分析文档内容"""
        pass

    @abstractmethod
    async def generate_summary(
        self,
        content: str,
        results: List[CheckResult]
    ) -> str:
        """生成整体总结"""
        pass

    def _get_dimension_prompt(self, dimension: CheckDimension, custom_rules: Optional[str] = None) -> str:
        """获取检测维度对应的提示词"""
        prompts = {
            CheckDimension.FORMAT: """
你是一个专业的文档格式审核专家。请对文档进行**严格的格式规范检查**，逐条找出具体问题。

## 检查清单

### 1. 标题与结构
- 标题层级是否清晰（一级标题→二级标题→三级标题）
- 是否存在标题跳级（如一级直接到三级）
- 标题编号是否连续一致（1.1, 1.2, 1.3 还是 1.1, 1.3, 1.5）
- 标题字号/样式是否统一

### 2. 段落与排版
- 段落是否有合理的首行缩进
- 段落间距是否一致
- 是否有过长的段落（超过200字建议分段）
- 空行使用是否规范（不应连续多个空行）

### 3. 列表与表格
- 列表符号是否统一（全用●或全用-）
- 多级列表层级是否清晰
- 表格是否有表头
- 表格内容是否对齐

### 4. 标点与符号
- 中英文标点是否混用（如中文用英文逗号,）
- 引号使用是否正确（""还是""）
- 省略号是否规范（…还是...）
- 数字与单位之间是否有空格

### 5. 字体与排版
- 正文字体是否统一
- 是否有不当的加粗/斜体/下划线
- 行间距是否一致
- 页边距是否合理

## 评分标准
- 90-100分：格式规范，最多1-2个小问题
- 75-89分：有一些格式问题，但不影响阅读
- 60-74分：格式问题较多，影响文档专业性
- 60分以下：格式混乱，需要全面整改
""",
            CheckDimension.CONTENT: """
你是一个专业的内容质量审核专家。请对文档进行**内容质量深度检查**，找出具体问题。

## 检查清单

### 1. 文字质量
- 是否有错别字（如：的地得混用、形近字错误）
- 是否有语病（如：主语缺失、搭配不当、成分残缺）
- 是否有重复啰嗦的表达
- 标点符号是否正确使用

### 2. 表述清晰度
- 句子是否过长难以理解（超过50字的长句）
- 是否有歧义表达
- 专业术语是否首次出现时有解释
- 缩写词是否有说明（首次出现应写全称）

### 3. 内容完整性
- 文档是否有明确的开头、正文、结尾
- 重要概念是否有充分解释
- 是否有未完成的句子或段落（如："待补充"、"TBD"）
- 关键信息是否遗漏

### 4. 语言风格
- 语气是否一致（正式/非正式）
- 人称是否统一（第一人称/第三人称）
- 时态是否一致
- 中英文混排是否合理

### 5. 数据与事实
- 数据是否有来源说明
- 日期格式是否统一
- 数字精度是否一致（如小数点位数）
- 单位是否正确且一致

## 评分标准
- 90-100分：内容质量优秀，表述清晰准确
- 75-89分：有少量问题，整体质量良好
- 60-74分：问题较多，需要修改润色
- 60分以下：内容质量差，需要重写
""",
            CheckDimension.LOGIC: """
你是一个专业的逻辑分析专家。请对文档进行**逻辑一致性深度检查**，找出矛盾和问题。

## 检查清单

### 1. 前后一致性
- 同一概念的描述是否前后一致
- 数据引用是否前后矛盾
- 时间线是否合理（不应出现时间倒流）
- 人物/角色描述是否一致

### 2. 因果逻辑
- 因果关系是否成立
- 论证过程是否充分
- 结论是否有足够的前提支撑
- 是否存在逻辑跳跃

### 3. 数据一致性
- 同一数据在不同位置引用是否一致
- 合计数是否等于分项之和
- 百分比相加是否为100%
- 图表数据与正文描述是否一致

### 4. 引用与依赖
- 引用的章节/图表是否存在
- 引用编号是否正确
- 交叉引用是否有效
- 参考文献是否完整

### 5. 结构逻辑
- 章节顺序是否合理
- 是否存在内容重复
- 递进关系是否正确
- 总结是否涵盖正文要点

## 评分标准
- 90-100分：逻辑严密，无明显矛盾
- 75-89分：有小的逻辑瑕疵，不影响理解
- 60-74分：存在明显逻辑问题，需要修正
- 60分以下：逻辑混乱，需要重新梳理
""",
            CheckDimension.SENSITIVE: """
你是一个专业的信息安全与合规审核专家。请对文档进行**敏感信息安全检查**，找出风险点。

## 检查清单

### 1. 个人身份信息
- 是否包含身份证号码（18位或15位数字）
- 是否包含手机号码（11位数字）
- 是否包含银行卡号
- 是否包含详细住址
- 是否包含电子邮箱
- 是否包含真实姓名+其他个人信息组合

### 2. 财务敏感信息
- 是否包含具体薪资数额
- 是否包含公司财务数据
- 是否包含合同金额
- 是否包含成本/利润等商业数据

### 3. 商业机密
- 是否包含未公开的产品计划
- 是否包含内部系统架构
- 是否包含客户名单
- 是否包含竞争对手分析
- 是否包含核心算法/技术细节

### 4. 账号密码
- 是否包含系统账号
- 是否包含密码/密钥
- 是否包含API Key/Token
- 是否包含内部系统URL

### 5. 不当内容
- 是否包含歧视性言论
- 是否包含政治敏感内容
- 是否包含虚假信息
- 是否包含负面评价（人身攻击）

## 风险等级说明
- error（高风险）：包含明确的敏感信息，必须删除或脱敏
- warning（中风险）：可能包含敏感信息，建议复核
- info（低风险）：存在潜在风险，建议注意

## 评分标准
- 90-100分：未发现敏感信息
- 75-89分：有低风险信息，建议注意
- 60-74分：存在中等风险，需要处理
- 60分以下：有高风险敏感信息，必须立即处理
""",
            CheckDimension.COMPLIANCE: """
你是一个专业的合规审核专家。请对文档进行**合规性检查**，确保符合规范要求。

## 检查清单

### 1. 版权与引用
- 引用内容是否标注来源
- 图片是否有版权说明
- 数据来源是否注明
- 是否涉及抄袭/未授权使用

### 2. 格式规范
- 是否符合行业标准文档格式
- 是否有必要的文档要素（标题、日期、版本、作者）
- 是否有目录（长文档）
- 是否有修订历史

### 3. 法律合规
- 是否符合相关法律法规要求
- 免责声明是否完整
- 是否有必要的授权说明
- 隐私声明是否到位

### 4. 专业规范
- 术语使用是否符合行业标准
- 度量单位是否使用国际标准
- 日期格式是否规范（YYYY-MM-DD）
- 数字格式是否规范（千分位分隔）

### 5. 文档管理
- 是否有文档编号
- 是否有版本号
- 是否有生效日期
- 是否有审核人/审批人

## 评分标准
- 90-100分：完全合规
- 75-89分：基本合规，有小的改进空间
- 60-74分：存在合规风险，需要完善
- 60分以下：严重不合规，需要全面整改
"""
        }

        base_prompt = prompts.get(dimension, "请全面审核以下文档内容。")

        if custom_rules:
            base_prompt += f"\n\n## 📌 额外检查要求（重要）\n{custom_rules}"

        base_prompt += """

## 输出格式要求

请以 JSON 格式返回检测结果，格式如下：
{
    "score": 85,
    "summary": "整体检测总结（50字以内）",
    "issues": [
        {
            "severity": "error",
            "location": "第X段/第X章/标题X",
            "description": "具体问题描述",
            "suggestion": "修改建议"
        },
        {
            "severity": "warning",
            "location": "具体位置",
            "description": "问题描述",
            "suggestion": "改进建议"
        }
    ]
}

## 严重程度说明
- error（错误）：必须修改的严重问题
- warning（警告）：建议修改的问题
- info（提示）：可以改进的小问题

## 注意事项
1. 每个问题必须指出**具体位置**，如"第3段"、"表格2"、"1.2节"
2. 问题描述要**具体明确**，指出哪里有问题
3. 修改建议要**可操作**，告诉用户如何修改
4. 根据问题数量和严重程度合理打分

只返回 JSON，不要其他内容。
"""
        return base_prompt

    def _parse_result(self, response: str, dimension: CheckDimension) -> CheckResult:
        """解析 AI 返回的结果"""
        try:
            # 尝试提取 JSON
            response = response.strip()

            # 处理 markdown 代码块
            if "```" in response:
                # 找到 JSON 内容
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
                if json_match:
                    response = json_match.group(1).strip()

            # 尝试找到 JSON 对象
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1:
                response = response[start_idx:end_idx + 1]

            data = json.loads(response)

            issues = []
            for issue_data in data.get("issues", []):
                # 解析严重程度，提供默认值
                severity_str = issue_data.get("severity", "info").lower()
                if severity_str not in ["error", "warning", "info"]:
                    severity_str = "info"

                issues.append(Issue(
                    dimension=dimension,
                    severity=Severity(severity_str),
                    location=issue_data.get("location", "未指定位置"),
                    description=issue_data.get("description", ""),
                    suggestion=issue_data.get("suggestion", "")
                ))

            # 计算合理的分数
            score = float(data.get("score", 80))
            # 确保分数在合理范围内
            score = max(0, min(100, score))

            # 如果有问题但分数过高，适当调整
            if issues:
                error_count = sum(1 for i in issues if i.severity == Severity.ERROR)
                warning_count = sum(1 for i in issues if i.severity == Severity.WARNING)

                # 根据问题数量调整最高分
                max_score = 100 - (error_count * 10) - (warning_count * 5)
                score = min(score, max_score)

            return CheckResult(
                dimension=dimension,
                score=score,
                summary=data.get("summary", "检测完成"),
                issues=issues
            )
        except json.JSONDecodeError as e:
            # JSON 解析失败
            return CheckResult(
                dimension=dimension,
                score=70,
                summary=f"检测完成，但结果格式异常",
                issues=[Issue(
                    dimension=dimension,
                    severity=Severity.INFO,
                    location="系统",
                    description=f"AI 返回结果解析异常: {str(e)[:100]}",
                    suggestion="建议重新检测"
                )]
            )
        except Exception as e:
            # 其他异常
            return CheckResult(
                dimension=dimension,
                score=70,
                summary=f"检测过程出现异常",
                issues=[Issue(
                    dimension=dimension,
                    severity=Severity.WARNING,
                    location="系统",
                    description=f"检测异常: {str(e)[:100]}",
                    suggestion="建议重新检测或联系管理员"
                )]
            )


class OpenAIProvider(BaseAIProvider):
    """OpenAI 实现"""

    def __init__(self):
        from openai import AsyncOpenAI
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model

    async def analyze(
        self,
        content: str,
        dimension: CheckDimension,
        custom_rules: Optional[str] = None
    ) -> CheckResult:
        prompt = self._get_dimension_prompt(dimension, custom_rules)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请检测以下文档内容：\n\n{content}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        return self._parse_result(result_text, dimension)

    async def generate_summary(
        self,
        content: str,
        results: List[CheckResult]
    ) -> str:
        # 统计问题数量
        total_errors = sum(sum(1 for i in r.issues if i.severity == Severity.ERROR) for r in results)
        total_warnings = sum(sum(1 for i in r.issues if i.severity == Severity.WARNING) for r in results)
        total_infos = sum(sum(1 for i in r.issues if i.severity == Severity.INFO) for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 0

        results_text = "\n".join([
            f"- {r.dimension.value}: 得分 {r.score:.0f}分, {r.summary}"
            for r in results
        ])

        stats_text = f"问题统计：错误 {total_errors} 个，警告 {total_warnings} 个，提示 {total_infos} 个，平均得分 {avg_score:.0f} 分"

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": """你是一个专业的文档审核专家。请根据检测结果生成简洁的整体评估总结。
要求：1.给出整体评价 2.指出主要问题 3.给出改进建议 4.控制在150字以内"""},
                {"role": "user", "content": f"各维度检测结果：\n{results_text}\n\n{stats_text}"}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude 实现"""

    def __init__(self):
        from anthropic import AsyncAnthropic
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    async def analyze(
        self,
        content: str,
        dimension: CheckDimension,
        custom_rules: Optional[str] = None
    ) -> CheckResult:
        prompt = self._get_dimension_prompt(dimension, custom_rules)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": f"{prompt}\n\n请检测以下文档内容：\n\n{content}"}
            ]
        )

        result_text = response.content[0].text
        return self._parse_result(result_text, dimension)

    async def generate_summary(
        self,
        content: str,
        results: List[CheckResult]
    ) -> str:
        total_errors = sum(sum(1 for i in r.issues if i.severity == Severity.ERROR) for r in results)
        total_warnings = sum(sum(1 for i in r.issues if i.severity == Severity.WARNING) for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 0

        results_text = "\n".join([
            f"- {r.dimension.value}: 得分 {r.score:.0f}分, {r.summary}"
            for r in results
        ])

        stats_text = f"问题统计：错误 {total_errors} 个，警告 {total_warnings} 个，平均得分 {avg_score:.0f} 分"

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"你是一个专业的文档审核专家。请根据检测结果生成简洁的整体评估总结（150字以内），包括整体评价、主要问题、改进建议。\n\n各维度检测结果：\n{results_text}\n\n{stats_text}"}
            ]
        )

        return response.content[0].text


class QwenProvider(BaseAIProvider):
    """通义千问实现（使用 OpenAI 兼容接口）"""

    def __init__(self):
        from openai import AsyncOpenAI
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.qwen_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = settings.qwen_model

    async def analyze(
        self,
        content: str,
        dimension: CheckDimension,
        custom_rules: Optional[str] = None
    ) -> CheckResult:
        prompt = self._get_dimension_prompt(dimension, custom_rules)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"请检测以下文档内容：\n\n{content}"}
            ],
            temperature=0.3
        )

        result_text = response.choices[0].message.content
        return self._parse_result(result_text, dimension)

    async def generate_summary(
        self,
        content: str,
        results: List[CheckResult]
    ) -> str:
        total_errors = sum(sum(1 for i in r.issues if i.severity == Severity.ERROR) for r in results)
        total_warnings = sum(sum(1 for i in r.issues if i.severity == Severity.WARNING) for r in results)
        total_infos = sum(sum(1 for i in r.issues if i.severity == Severity.INFO) for r in results)
        avg_score = sum(r.score for r in results) / len(results) if results else 0

        results_text = "\n".join([
            f"- {r.dimension.value}: 得分 {r.score:.0f}分, {r.summary}"
            for r in results
        ])

        stats_text = f"问题统计：错误 {total_errors} 个，警告 {total_warnings} 个，提示 {total_infos} 个，平均得分 {avg_score:.0f} 分"

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": """你是一个专业的文档审核专家。请根据检测结果生成简洁的整体评估总结。
要求：1.给出整体评价 2.指出主要问题 3.给出改进建议 4.控制在150字以内"""},
                {"role": "user", "content": f"各维度检测结果：\n{results_text}\n\n{stats_text}"}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """获取 AI 提供商实例"""
    settings = get_settings()
    provider = provider_name or settings.default_ai_provider

    if provider == "openai":
        return OpenAIProvider()
    elif provider == "anthropic":
        try:
            # 先测试能否导入
            import anthropic
            return AnthropicProvider()
        except ImportError:
            raise ValueError("anthropic 模块未安装，请运行: pip install anthropic，或选择其他 AI 提供商")
    elif provider == "qwen":
        return QwenProvider()
    else:
        raise ValueError(f"不支持的 AI 提供商: {provider}，可选: openai, anthropic, qwen")
