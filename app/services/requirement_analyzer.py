"""
需求文档分析服务 - 检测需求完整性、场景覆盖、描述质量
"""
import json
from typing import Optional, List
from datetime import datetime

from app.config import get_settings
from app.models import (
    RequirementAnalysisResult, RequirementItem,
    TestCase, TestStep, TestCaseGenerationResult,
    TestCasePriority, TestCaseType
)
from app.services.ai_providers import get_ai_provider


class RequirementAnalyzer:
    """需求文档分析器"""

    def __init__(self, ai_provider_name: Optional[str] = None):
        self.ai_provider = get_ai_provider(ai_provider_name)

    async def analyze_requirements(self, content: str) -> RequirementAnalysisResult:
        """分析需求文档"""
        prompt = """你是一个拥有10年经验的**业务分析师和产品经理**。请站在业务视角对需求文档进行深度分析，重点关注**业务逻辑、用户体验、商业价值**层面的问题。

## 🎯 分析视角（业务优先）

你需要像一个真正理解业务的产品经理一样思考：
- 这个功能解决了用户什么痛点？
- 业务流程是否完整闭环？
- 会不会有用户被"卡住"的情况？
- 这个设计符合行业惯例吗？
- 运营和客服能支撑吗？

## 📋 业务分析清单（针对每个功能点）

### 1. 业务流程完整性
- **用户旅程**：用户从哪里来？完成后去哪里？中途放弃怎么办？
- **业务闭环**：流程是否有始有终？是否有"断头路"？
- **角色覆盖**：涉及哪些角色（用户/商家/运营/客服）？各角色的操作是否都说清楚了？
- **状态流转**：业务状态有哪些？状态之间如何转换？能否逆向操作？

### 2. 业务规则清晰度
- **核心规则**：业务的关键判断逻辑是什么？条件是否明确？
- **金额计算**：涉及金额时，计算公式是否清晰？精度如何处理？
- **时间规则**：有效期、过期处理、时区问题是否考虑？
- **数量限制**：业务上的限制条件是否说明？（如：每人限购X件）

### 3. 异常场景与边界
- **业务异常**：库存不足、余额不够、资格不符等业务场景如何处理？
- **操作冲突**：多人同时操作怎么办？重复提交怎么办？
- **数据边界**：0的情况、负数的情况、超大数的情况
- **时间边界**：跨天、跨月、节假日等特殊时间点

### 4. 用户体验考量
- **操作反馈**：用户操作后能看到什么反馈？
- **错误引导**：出错时用户知道该怎么办吗？
- **撤销回退**：用户操作错了能撤销吗？
- **新手引导**：首次使用的用户能顺利完成吗？

### 5. 运营支撑能力
- **数据统计**：运营需要看哪些数据？是否支持？
- **人工干预**：需要人工处理的场景有哪些？后台功能是否支持？
- **客诉处理**：出问题时客服如何查询和处理？
- **灰度上线**：是否需要分批放量？如何控制？

## 📤 输出格式（JSON）：

{
    "total_requirements": 3,
    "requirements": [
        {
            "req_id": "REQ-001",
            "title": "会员积分兑换功能",
            "description": "用户可用积分兑换优惠券或礼品",
            "priority": "高",
            "issues": [
                "[业务流程断点] 积分不足时的用户引导缺失：用户看到想兑换的商品但积分不够，没有说明如何引导用户去赚取积分",
                "[规则不明确] 积分有效期规则未说明：积分是否会过期？过期前是否提醒？即将过期的积分是否优先使用？",
                "[并发场景遗漏] 热门商品抢兑场景未考虑：限量商品多人同时兑换时的库存扣减和失败处理",
                "[逆向流程缺失] 兑换后的退换规则未说明：礼品有质量问题怎么办？优惠券兑换后能否退回积分？",
                "[运营能力缺失] 积分发放和扣减的后台管理功能未提及：运营如何手动补发积分？如何查询用户积分明细？"
            ],
            "suggestions": [
                "补充积分不足引导：显示'还差X积分'，提供'去赚积分'入口，展示积分获取途径",
                "明确积分有效期：积分自获得之日起12个月有效，到期前30天短信/push提醒，使用时优先扣除即将过期积分",
                "添加库存锁定机制：用户点击兑换后锁定库存5分钟，超时未支付自动释放，同时给出排队提示",
                "补充退换规则：实物商品签收后7天内可申请退换，优惠券一经兑换不可退回",
                "增加运营后台需求：支持按用户ID查询积分明细，支持批量发放积分，支持积分冻结/解冻"
            ]
        },
        {
            "req_id": "REQ-002",
            "title": "订单取消功能",
            "description": "用户可以取消未发货的订单",
            "priority": "高",
            "issues": [
                "[状态定义不清] '未发货'的准确定义不明确：是商家未点发货？还是物流未揽收？商家已打包但未发货算什么状态？",
                "[资金流转遗漏] 退款规则未说明：取消后多久退款？退到哪里？使用了优惠券/积分如何处理？",
                "[库存回滚缺失] 取消订单后的库存处理未说明：库存是否立即回滚？是否影响其他用户下单？",
                "[通知机制缺失] 取消后的通知策略未说明：是否通知商家？通知方式是什么？商家多久内需确认？",
                "[售后衔接问题] 取消和售后的关系未说明：已申请售后的订单能否取消？取消后的售后单如何处理？"
            ],
            "suggestions": [
                "明确状态定义：'未发货'=商家未点击发货按钮；'已发货待揽收'状态下取消需走拦截流程",
                "补充退款规则：取消成功后24小时内原路退回；优惠券退回账户（有效期顺延7天）；积分即时返还",
                "补充库存规则：普通商品取消后库存即时回滚；秒杀/限购商品回滚后不再开放",
                "补充通知机制：取消后实时push通知商家，商家2小时内未确认自动同意，超时升级至平台处理",
                "明确售后关系：已有进行中售后单的订单不可整单取消，需先完成或关闭售后"
            ]
        }
    ],
    "completeness_score": 55,
    "scenario_coverage_score": 45,
    "description_quality_score": 60,
    "testability_score": 50,
    "overall_score": 52,
    "summary": "该文档共包含X个功能点。主要问题：1）X个功能的业务流程存在断点，用户可能被卡住 2）X个功能缺少异常场景处理，可能导致客诉 3）运营后台支撑能力普遍不足。建议优先补充核心功能的异常处理和逆向流程。",
    "improvement_suggestions": [
        "[高优先级] 为每个功能梳理完整的用户旅程，确保流程闭环无断点，特别是异常情况下的用户引导",
        "[高优先级] 补充资金相关规则：涉及金额的功能必须说明计算公式、精度处理、退款规则",
        "[中优先级] 每个功能补充状态流转图，明确各状态的定义和转换条件，特别是逆向状态",
        "[中优先级] 补充运营后台需求，确保每个业务功能都有对应的后台查询和处理能力",
        "[建议] 组织业务评审会议，邀请客服、运营一起评审，提前发现实际运营中可能遇到的问题"
    ]
}

## ⚠️ 关键要求：

1. **业务视角优先**：问题要从业务影响角度描述（如"用户会被卡住"、"可能导致客诉"），而不是纯技术视角
2. **问题类型**使用以下标签：
   - `[业务流程断点]` - 用户旅程中断、流程不闭环
   - `[规则不明确]` - 业务规则、计算逻辑不清晰
   - `[状态定义不清]` - 业务状态及流转规则模糊
   - `[并发场景遗漏]` - 多用户/多操作冲突未考虑
   - `[逆向流程缺失]` - 退款/退货/取消/撤销等逆向操作未说明
   - `[运营能力缺失]` - 缺少运营后台/数据统计/人工干预能力
   - `[通知机制缺失]` - 用户/商家/运营的通知提醒未说明
   - `[异常处理缺失]` - 业务异常场景（库存不足、余额不够等）未处理
   - `[边界场景遗漏]` - 特殊情况（0值、极限值、特殊时间点）未考虑
3. **建议要可落地**：建议要具体到业务规则（如"12个月有效期"、"30天提醒"），而不是泛泛而谈
4. **严禁雷同**：每个需求的issues和suggestions必须针对其具体业务内容，不能复制粘贴

只返回 JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请分析以下需求文档：\n\n{content}"}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            result_text = self._clean_json(result_text)
            data = json.loads(result_text)

            # 解析需求项
            requirements = []
            for req in data.get("requirements", []):
                requirements.append(RequirementItem(
                    req_id=req.get("req_id", ""),
                    title=req.get("title", ""),
                    description=req.get("description", ""),
                    priority=req.get("priority"),
                    issues=req.get("issues", []),
                    suggestions=req.get("suggestions", [])
                ))

            return RequirementAnalysisResult(
                total_requirements=data.get("total_requirements", len(requirements)),
                analyzed_requirements=requirements,
                completeness_score=float(data.get("completeness_score", 0)),
                scenario_coverage_score=float(data.get("scenario_coverage_score", 0)),
                description_quality_score=float(data.get("description_quality_score", 0)),
                testability_score=float(data.get("testability_score", 0)),
                overall_score=float(data.get("overall_score", 0)),
                summary=data.get("summary", ""),
                improvement_suggestions=data.get("improvement_suggestions", [])
            )

        except Exception as e:
            raise Exception(f"需求分析失败: {str(e)}")

    async def generate_test_cases(self, content: str, document_id: str) -> TestCaseGenerationResult:
        """根据需求文档生成测试用例"""
        prompt = """你是一个拥有15年经验的资深测试架构师。请根据需求文档为每个功能点生成**全面、详细、具体、可执行**的测试用例。

## 🎯 核心目标
为每个功能点生成**至少20-30个测试用例**，确保全方位覆盖各种测试场景。用例要具体、可执行、有真实数据。

## 测试用例设计原则

1. **具体化**：每个步骤必须具体到可以直接执行，不能有模糊描述
2. **数据驱动**：必须提供具体的测试数据（使用真实感的数据如姓名、手机号、邮箱等）
3. **全面覆盖**：每个功能必须覆盖所有测试类型
4. **可验证**：预期结果必须明确，能够判断测试是否通过
5. **场景丰富**：考虑各种用户角色、设备、网络环境等

## 📋 必须覆盖的测试类型（每个功能都要有）

### 1️⃣ 功能测试（P0/P1）- 至少5个用例
- 正常流程完整走通（主流程）
- 使用有效数据验证核心功能
- 多种有效输入组合测试
- 不同用户角色测试（普通用户/VIP/管理员）
- 不同业务场景测试（首次使用/重复使用）

### 2️⃣ 反向/异常测试（P1/P2）- 至少6个用例
- 必填项为空时的提示
- 数据格式错误时的处理（邮箱格式、手机号格式等）
- 权限不足时的提示
- 业务规则不满足时的处理（余额不足、库存不足等）
- 网络异常/超时处理（断网、弱网、请求超时）
- 并发操作冲突处理（同时提交、重复点击）
- 服务端异常处理（500错误、接口超时）

### 3️⃣ 边界测试（P1/P2）- 至少5个用例
- 最小值测试（0、1、最小长度）
- 最大值测试（最大长度、最大数量）
- 边界值-1和+1测试
- 空值、null值测试
- 特殊字符处理（中文、emoji、特殊符号）
- 超长文本测试

### 4️⃣ 安全测试（P1/P2）- 至少6个用例
- **SQL注入测试**：' OR '1'='1、1; DROP TABLE users--、UNION SELECT
- **XSS跨站脚本测试**：<script>alert('xss')</script>、<img onerror="alert(1)">、javascript:alert(1)
- **CSRF跨站请求伪造测试**：验证Token机制、Referer校验
- **认证授权测试**：未登录访问、Token过期、Token篡改、伪造Token
- **权限越权测试**：垂直越权（普通用户访问管理员功能）、水平越权（访问他人数据）
- **敏感数据测试**：密码是否明文传输、敏感信息是否脱敏显示、日志是否泄露敏感信息
- **暴力破解测试**：密码错误次数限制、验证码机制

### 5️⃣ 兼容性测试（P2/P3）- 至少4个用例
- **浏览器兼容性**：Chrome、Firefox、Safari、Edge、IE11
- **移动端兼容性**：iOS Safari、Android Chrome、微信内置浏览器、支付宝内置浏览器
- **分辨率兼容性**：1920x1080、1366x768、1280x720、375x667(iPhone)、414x896(iPhone Plus)
- **系统兼容性**：Windows、MacOS、iOS、Android

### 6️⃣ 接口测试（P1/P2）- 至少5个用例
- **接口契约测试**：请求参数校验、响应格式校验、必填参数缺失
- **接口安全测试**：无Token调用、错误Token调用、过期Token调用
- **接口性能测试**：响应时间是否在可接受范围内（<200ms）
- **接口幂等性测试**：重复调用是否产生副作用
- **接口异常测试**：参数类型错误、参数值越界、接口不存在

### 7️⃣ UI测试（P2/P3）- 至少4个用例
- **UI交互测试**：按钮可点击、输入框可输入、下拉框可选择、复选框/单选框
- **UI响应式测试**：不同屏幕尺寸下的显示效果
- **UI状态测试**：Loading状态、空数据状态、错误状态、禁用状态
- **UI无障碍测试**：键盘导航、Tab顺序、屏幕阅读器兼容

### 8️⃣ 性能测试（P2/P3）- 至少4个用例
- **负载测试**：正常负载下的响应时间
- **并发测试**：100/500/1000用户同时操作
- **压力测试**：超出系统承载能力时的表现
- **大数据量测试**：列表10000+条数据时的加载表现
- **内存泄漏测试**：长时间运行后的内存占用

### 9️⃣ 数据测试（P1/P2）- 至少4个用例
- **数据一致性测试**：前端显示与数据库数据一致
- **数据完整性测试**：必要字段是否正确保存
- **数据回滚测试**：操作失败时数据是否正确回滚
- **数据隔离测试**：不同用户/租户的数据是否隔离
- **数据备份恢复测试**：数据备份和恢复是否正常

### 🔟 业务流程测试（P0/P1）- 至少3个用例
- **完整业务流程**：从开始到结束的完整流程
- **中断恢复测试**：流程中断后能否继续
- **逆向流程测试**：取消、退款、撤销等逆向操作

## 测试数据示例库（请使用类似真实数据）

- 手机号：13812345678、13987654321、18600001111
- 邮箱：zhangsan@example.com、test.user@company.cn
- 姓名：张三、李四、王小明、赵丽颖
- 身份证：110101199003071234
- 银行卡：6222021234567890123
- 金额：0.01、99.99、1000.00、99999.99
- 地址：北京市朝阳区建国路88号SOHO现代城A座1001室
- 用户名：test_user_001、admin、zhangsan123
- 密码：Test@123456、Abc#12345、Pass!word99

## 输出格式（JSON）：

{
    "test_cases": [
        {
            "case_id": "TC-模块名-001",
            "requirement_id": "REQ-001",
            "title": "【测试类型-子类型】具体的测试标题描述",
            "priority": "P0/P1/P2/P3",
            "case_type": "测试类型",
            "precondition": "详细的前置条件，包含具体数据",
            "steps": [
                {"step_number": 1, "action": "具体操作描述，包含具体数据", "expected_result": "具体的预期结果"}
            ],
            "test_data": "具体的测试数据",
            "tags": ["标签1", "标签2"]
        }
    ],
    "coverage_summary": "覆盖情况统计描述"
}

## ⚠️ 重要要求：

1. **数量要求**：每个功能点至少生成20个测试用例，必须覆盖上述所有测试类型
2. case_id 格式：TC-功能模块-序号，如 TC-LOGIN-001、TC-ORDER-001、TC-PAY-001
3. title 必须以【测试类型-子类型】开头，如【功能-正向】【安全-SQL注入】【兼容-移动端】【接口-契约】【UI-交互】【性能-并发】【边界-最大值】【异常-网络超时】
4. steps 中的 action 必须具体到"输入什么内容"、"点击什么按钮"，使用真实的测试数据
5. expected_result 必须具体到"显示什么文字"、"跳转到什么页面"、"返回什么状态码"
6. test_data 必须提供具体的测试数据值
7. precondition 必须包含具体的前置数据和状态
8. **测试类型(case_type)可选值**：
   - 基础类型：functional, boundary, exception, smoke, regression
   - 安全类型：security, sql_injection, xss, csrf, auth, permission, sensitive_data
   - 兼容类型：compatibility, browser_compat, mobile_compat, resolution_compat
   - 接口类型：api, api_contract, api_security, api_performance
   - UI类型：ui, ui_interaction, ui_responsive, ui_accessibility
   - 性能类型：performance, load, stress, concurrent
   - 数据类型：data, database, cache
   - 其他：integration, usability, reliability, recovery, localization

只返回 JSON，不要其他内容。
"""

        try:
            response = await self.ai_provider.client.chat.completions.create(
                model=self.ai_provider.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"请根据以下需求文档生成测试用例：\n\n{content}"}
                ],
                temperature=0.3
            )

            result_text = response.choices[0].message.content
            result_text = self._clean_json(result_text)
            data = json.loads(result_text)

            # 解析测试用例
            test_cases = []
            for tc in data.get("test_cases", []):
                steps = []
                for step in tc.get("steps", []):
                    steps.append(TestStep(
                        step_number=step.get("step_number", 1),
                        action=step.get("action", ""),
                        expected_result=step.get("expected_result", "")
                    ))

                # 解析优先级
                priority_map = {"P0": TestCasePriority.P0, "P1": TestCasePriority.P1,
                               "P2": TestCasePriority.P2, "P3": TestCasePriority.P3}
                priority = priority_map.get(tc.get("priority", "P2"), TestCasePriority.P2)

                # 解析类型
                type_map = {
                    "functional": TestCaseType.FUNCTIONAL,
                    "boundary": TestCaseType.BOUNDARY,
                    "exception": TestCaseType.EXCEPTION,
                    "performance": TestCaseType.PERFORMANCE,
                    "security": TestCaseType.SECURITY,
                    "compatibility": TestCaseType.COMPATIBILITY,
                    "usability": TestCaseType.USABILITY,
                    "api": TestCaseType.API,
                    "ui": TestCaseType.UI,
                    "data": TestCaseType.DATA,
                    "regression": TestCaseType.REGRESSION,
                    "smoke": TestCaseType.SMOKE,
                    "integration": TestCaseType.INTEGRATION,
                    # 安全测试子类型
                    "sql_injection": TestCaseType.SQL_INJECTION,
                    "xss": TestCaseType.XSS,
                    "csrf": TestCaseType.CSRF,
                    "auth": TestCaseType.AUTH,
                    "permission": TestCaseType.PERMISSION,
                    "sensitive_data": TestCaseType.SENSITIVE_DATA,
                    # 兼容性测试子类型
                    "mobile_compat": TestCaseType.MOBILE_COMPAT,
                    "browser_compat": TestCaseType.BROWSER_COMPAT,
                    "resolution_compat": TestCaseType.RESOLUTION_COMPAT,
                    # 接口测试子类型
                    "api_contract": TestCaseType.API_CONTRACT,
                    "api_security": TestCaseType.API_SECURITY,
                    "api_performance": TestCaseType.API_PERFORMANCE,
                    # UI测试子类型
                    "ui_interaction": TestCaseType.UI_INTERACTION,
                    "ui_responsive": TestCaseType.UI_RESPONSIVE,
                    "ui_accessibility": TestCaseType.UI_ACCESSIBILITY,
                    # 性能测试子类型
                    "load": TestCaseType.LOAD,
                    "stress": TestCaseType.STRESS,
                    "concurrent": TestCaseType.CONCURRENT,
                    # 其他类型
                    "reliability": TestCaseType.RELIABILITY,
                    "recovery": TestCaseType.RECOVERY,
                    "upgrade": TestCaseType.UPGRADE,
                    "localization": TestCaseType.LOCALIZATION,
                    "database": TestCaseType.DATABASE,
                    "cache": TestCaseType.CACHE,
                    "log": TestCaseType.LOG,
                    "monitor": TestCaseType.MONITOR,
                }
                case_type = type_map.get(tc.get("case_type", "functional"), TestCaseType.FUNCTIONAL)

                test_cases.append(TestCase(
                    case_id=tc.get("case_id", ""),
                    requirement_id=tc.get("requirement_id"),
                    title=tc.get("title", ""),
                    priority=priority,
                    case_type=case_type,
                    precondition=tc.get("precondition"),
                    steps=steps,
                    test_data=tc.get("test_data"),
                    tags=tc.get("tags", [])
                ))

            return TestCaseGenerationResult(
                document_id=document_id,
                total_cases=len(test_cases),
                test_cases=test_cases,
                coverage_summary=data.get("coverage_summary", ""),
                generated_at=datetime.now()
            )

        except Exception as e:
            raise Exception(f"测试用例生成失败: {str(e)}")

    def _clean_json(self, text: str) -> str:
        """清理 JSON 文本"""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:-1] if lines[-1] == "```" else lines[1:]
            text = "\n".join(lines)
        if text.startswith("json"):
            text = text[4:]
        return text.strip()
