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
为每个功能点生成**至少15-20个测试用例**，确保全方位覆盖各种测试场景。

## 测试用例设计原则

1. **具体化**：每个步骤必须具体到可以直接执行，不能有模糊描述
2. **数据驱动**：必须提供具体的测试数据（使用真实感的数据如姓名、手机号、邮箱等）
3. **全面覆盖**：每个功能必须覆盖所有测试类型
4. **可验证**：预期结果必须明确，能够判断测试是否通过
5. **场景丰富**：考虑各种用户角色、设备、网络环境等

## 📋 必须覆盖的测试类型（每个功能都要有）

## 📋 必须覆盖的测试类型（每个功能都要有）

### 1️⃣ 功能测试（P0/P1）- 至少3个用例
- 正常流程完整走通
- 使用有效数据验证核心功能
- 多种有效输入组合测试

### 2️⃣ 反向/异常测试（P1/P2）- 至少4个用例
- 必填项为空时的提示
- 数据格式错误时的处理
- 权限不足时的提示
- 业务规则不满足时的处理
- 网络异常/超时处理
- 并发操作冲突处理

### 3️⃣ 边界测试（P1/P2）- 至少3个用例
- 最小值、最大值测试
- 长度边界（刚好、超出一位）
- 数量边界（0个、1个、最大个数）
- 特殊字符处理

### 4️⃣ 安全测试（P1/P2）- 至少4个用例
- **SQL注入测试**：输入 ' OR '1'='1、1; DROP TABLE users-- 等
- **XSS跨站脚本测试**：输入 <script>alert('xss')</script>、<img onerror="alert(1)">
- **CSRF跨站请求伪造测试**：验证Token机制
- **认证授权测试**：未登录访问、Token过期、Token篡改
- **权限越权测试**：普通用户访问管理员功能、水平越权访问他人数据
- **敏感数据测试**：密码是否明文传输、敏感信息是否脱敏显示

### 5️⃣ 兼容性测试（P2/P3）- 至少3个用例
- **浏览器兼容性**：Chrome、Firefox、Safari、Edge
- **移动端兼容性**：iOS Safari、Android Chrome、微信内置浏览器
- **分辨率兼容性**：1920x1080、1366x768、375x667(iPhone)、414x896

### 6️⃣ 接口测试（P1/P2）- 至少3个用例
- **接口契约测试**：请求参数校验、响应格式校验
- **接口安全测试**：无Token调用、错误Token调用
- **接口性能测试**：响应时间是否在可接受范围内
- **接口幂等性测试**：重复调用是否产生副作用

### 7️⃣ UI测试（P2/P3）- 至少3个用例
- **UI交互测试**：按钮可点击、输入框可输入、下拉框可选择
- **UI响应式测试**：不同屏幕尺寸下的显示效果
- **UI无障碍测试**：键盘导航、屏幕阅读器兼容

### 8️⃣ 性能测试（P2/P3）- 至少2个用例
- **负载测试**：正常负载下的响应时间
- **并发测试**：多用户同时操作的表现
- **大数据量测试**：列表数据量大时的加载表现

### 9️⃣ 数据测试（P1/P2）- 至少2个用例
- **数据一致性测试**：前端显示与数据库数据一致
- **数据完整性测试**：必要字段是否正确保存
- **数据回滚测试**：操作失败时数据是否正确回滚

## 输出格式（JSON）：

{
    "test_cases": [
        {
            "case_id": "TC-LOGIN-001",
            "requirement_id": "REQ-001",
            "title": "【功能-正向】使用正确的手机号密码登录成功",
            "priority": "P0",
            "case_type": "functional",
            "precondition": "1. 用户已注册账号，手机号：13812345678，密码：Test@123456\\n2. 账号状态正常，未被锁定\\n3. 网络连接正常",
            "steps": [
                {"step_number": 1, "action": "打开登录页面 https://xxx.com/login", "expected_result": "显示登录页面，包含手机号、密码输入框和登录按钮"},
                {"step_number": 2, "action": "在手机号输入框输入：13812345678", "expected_result": "手机号正确显示，无报错提示"},
                {"step_number": 3, "action": "在密码输入框输入：Test@123456", "expected_result": "密码以●●●形式显示"},
                {"step_number": 4, "action": "点击【登录】按钮", "expected_result": "1. 按钮显示loading状态\\n2. 1-2秒内登录成功\\n3. 跳转到首页\\n4. 右上角显示用户头像和昵称"}
            ],
            "test_data": "手机号：13812345678，密码：Test@123456",
            "tags": ["登录", "P0", "冒烟测试", "功能测试"]
        },
        {
            "case_id": "TC-LOGIN-002",
            "requirement_id": "REQ-001", 
            "title": "【异常-反向】密码错误时显示错误提示并记录失败次数",
            "priority": "P1",
            "case_type": "exception",
            "precondition": "用户已注册，手机号：13812345678，正确密码为 Test@123456",
            "steps": [
                {"step_number": 1, "action": "打开登录页面", "expected_result": "显示登录页面"},
                {"step_number": 2, "action": "输入手机号：13812345678", "expected_result": "手机号正确显示"},
                {"step_number": 3, "action": "输入错误密码：WrongPass123", "expected_result": "密码以密文形式显示"},
                {"step_number": 4, "action": "点击【登录】按钮", "expected_result": "1. 提示'手机号或密码错误，还可尝试4次'\\n2. 停留在登录页面\\n3. 密码框自动清空\\n4. 手机号保留"}
            ],
            "test_data": "手机号：13812345678，错误密码：WrongPass123",
            "tags": ["登录", "异常测试", "P1"]
        },
        {
            "case_id": "TC-LOGIN-003",
            "requirement_id": "REQ-001",
            "title": "【边界】密码长度为最小值8位时正常登录",
            "priority": "P2",
            "case_type": "boundary",
            "precondition": "用户已注册，密码设置为8位：Aa@12345",
            "steps": [
                {"step_number": 1, "action": "打开登录页面", "expected_result": "显示登录页面"},
                {"step_number": 2, "action": "输入手机号和8位密码：Aa@12345", "expected_result": "输入成功"},
                {"step_number": 3, "action": "点击登录", "expected_result": "登录成功，跳转首页"}
            ],
            "test_data": "手机号：13812345678，8位密码：Aa@12345",
            "tags": ["登录", "边界测试", "P2"]
        },
        {
            "case_id": "TC-LOGIN-004",
            "requirement_id": "REQ-001",
            "title": "【安全-SQL注入】登录接口防SQL注入攻击",
            "priority": "P1",
            "case_type": "sql_injection",
            "precondition": "登录页面可正常访问",
            "steps": [
                {"step_number": 1, "action": "打开登录页面", "expected_result": "显示登录页面"},
                {"step_number": 2, "action": "在手机号输入框输入：' OR '1'='1' --", "expected_result": "输入被接受"},
                {"step_number": 3, "action": "在密码框输入任意内容：123456", "expected_result": "正常显示"},
                {"step_number": 4, "action": "点击登录", "expected_result": "1. 不会登录成功\\n2. 提示'手机号格式不正确'或'用户名密码错误'\\n3. 不会显示数据库错误信息"}
            ],
            "test_data": "SQL注入payload：' OR '1'='1' --",
            "tags": ["登录", "安全测试", "SQL注入", "P1"]
        },
        {
            "case_id": "TC-LOGIN-005",
            "requirement_id": "REQ-001",
            "title": "【安全-XSS】登录页面防XSS跨站脚本攻击",
            "priority": "P1",
            "case_type": "xss",
            "precondition": "登录页面可正常访问",
            "steps": [
                {"step_number": 1, "action": "打开登录页面", "expected_result": "显示登录页面"},
                {"step_number": 2, "action": "在手机号输入框输入：<script>alert('XSS')</script>", "expected_result": "输入被接受或被过滤"},
                {"step_number": 3, "action": "点击登录", "expected_result": "1. 不会弹出alert对话框\\n2. 页面正常显示\\n3. 脚本标签被转义或过滤"}
            ],
            "test_data": "XSS payload：<script>alert('XSS')</script>",
            "tags": ["登录", "安全测试", "XSS", "P1"]
        },
        {
            "case_id": "TC-LOGIN-006",
            "requirement_id": "REQ-001",
            "title": "【安全-认证】未登录状态访问需登录页面被拦截",
            "priority": "P0",
            "case_type": "auth",
            "precondition": "用户未登录，清除所有Cookie和本地存储",
            "steps": [
                {"step_number": 1, "action": "直接访问个人中心页面 https://xxx.com/user/profile", "expected_result": "1. 自动跳转到登录页面\\n2. URL带有redirect参数指向原页面"},
                {"step_number": 2, "action": "登录成功后", "expected_result": "自动跳转回个人中心页面"}
            ],
            "test_data": "无",
            "tags": ["登录", "安全测试", "认证授权", "P0"]
        },
        {
            "case_id": "TC-LOGIN-007",
            "requirement_id": "REQ-001",
            "title": "【兼容-浏览器】Chrome浏览器登录功能正常",
            "priority": "P2",
            "case_type": "browser_compat",
            "precondition": "使用Chrome浏览器（版本100+）",
            "steps": [
                {"step_number": 1, "action": "使用Chrome浏览器打开登录页面", "expected_result": "页面正常显示，无样式错乱"},
                {"step_number": 2, "action": "输入正确的手机号密码登录", "expected_result": "登录成功，功能正常"}
            ],
            "test_data": "Chrome 120版本",
            "tags": ["登录", "兼容性测试", "浏览器", "P2"]
        },
        {
            "case_id": "TC-LOGIN-008",
            "requirement_id": "REQ-001",
            "title": "【兼容-移动端】iPhone微信内置浏览器登录正常",
            "priority": "P2",
            "case_type": "mobile_compat",
            "precondition": "使用iPhone微信内置浏览器",
            "steps": [
                {"step_number": 1, "action": "在微信中打开登录页面链接", "expected_result": "页面正常显示，适配移动端"},
                {"step_number": 2, "action": "输入手机号密码登录", "expected_result": "软键盘正常弹出，登录成功"}
            ],
            "test_data": "iPhone 14, iOS 17, 微信8.0",
            "tags": ["登录", "兼容性测试", "移动端", "P2"]
        },
        {
            "case_id": "TC-LOGIN-009",
            "requirement_id": "REQ-001",
            "title": "【接口-契约】登录接口参数校验",
            "priority": "P1",
            "case_type": "api_contract",
            "precondition": "接口测试工具准备就绪（Postman/JMeter）",
            "steps": [
                {"step_number": 1, "action": "调用登录接口，不传手机号参数", "expected_result": "返回400，错误信息：'手机号不能为空'"},
                {"step_number": 2, "action": "调用登录接口，手机号传空字符串", "expected_result": "返回400，错误信息：'手机号格式不正确'"},
                {"step_number": 3, "action": "调用登录接口，手机号传非法格式12345", "expected_result": "返回400，错误信息：'手机号格式不正确'"}
            ],
            "test_data": "POST /api/login，缺少phone参数",
            "tags": ["登录", "接口测试", "参数校验", "P1"]
        },
        {
            "case_id": "TC-LOGIN-010",
            "requirement_id": "REQ-001",
            "title": "【UI-交互】登录按钮点击状态变化",
            "priority": "P2",
            "case_type": "ui_interaction",
            "precondition": "登录页面已打开",
            "steps": [
                {"step_number": 1, "action": "鼠标悬停在登录按钮上", "expected_result": "按钮颜色变深，显示手型光标"},
                {"step_number": 2, "action": "点击登录按钮（未输入信息）", "expected_result": "按钮无反应或提示必填项"},
                {"step_number": 3, "action": "输入完整信息后点击登录", "expected_result": "按钮显示loading状态，防止重复点击"}
            ],
            "test_data": "无",
            "tags": ["登录", "UI测试", "交互", "P2"]
        },
        {
            "case_id": "TC-LOGIN-011",
            "requirement_id": "REQ-001",
            "title": "【性能-并发】多用户同时登录系统稳定性",
            "priority": "P2",
            "case_type": "concurrent",
            "precondition": "准备100个测试账号，性能测试工具就绪",
            "steps": [
                {"step_number": 1, "action": "使用JMeter模拟100个用户同时登录", "expected_result": "所有请求正常处理"},
                {"step_number": 2, "action": "观察响应时间", "expected_result": "95%的请求响应时间小于2秒"},
                {"step_number": 3, "action": "观察错误率", "expected_result": "错误率低于1%"}
            ],
            "test_data": "100并发，持续1分钟",
            "tags": ["登录", "性能测试", "并发", "P2"]
        },
        {
            "case_id": "TC-LOGIN-012",
            "requirement_id": "REQ-001",
            "title": "【数据-一致性】登录后用户信息显示正确",
            "priority": "P1",
            "case_type": "data",
            "precondition": "数据库中用户昵称为'张三'，头像已设置",
            "steps": [
                {"step_number": 1, "action": "使用该账号登录", "expected_result": "登录成功"},
                {"step_number": 2, "action": "查看页面右上角用户信息", "expected_result": "显示昵称'张三'，头像正确显示"},
                {"step_number": 3, "action": "进入个人中心", "expected_result": "所有用户信息与数据库一致"}
            ],
            "test_data": "用户ID：10001，昵称：张三",
            "tags": ["登录", "数据测试", "一致性", "P1"]
        }
    ],
    "coverage_summary": "共生成X个测试用例，覆盖X个功能点。包含：功能测试X个、异常测试X个、边界测试X个、安全测试X个（SQL注入、XSS、认证授权）、兼容性测试X个（浏览器、移动端）、接口测试X个、UI测试X个、性能测试X个、数据测试X个。测试覆盖率：功能覆盖100%，安全覆盖90%，兼容性覆盖85%。"
}

## ⚠️ 重要要求：

1. **数量要求**：每个功能点至少生成15个测试用例，覆盖所有测试类型
2. case_id 格式：TC-功能模块-序号，如 TC-LOGIN-001、TC-ORDER-001
3. title 必须以【测试类型】开头，如【功能-正向】【安全-SQL注入】【兼容-移动端】【接口-契约】【UI-交互】【性能-并发】
4. steps 中的 action 必须具体到"输入什么内容"、"点击什么按钮"，使用真实的测试数据
5. expected_result 必须具体到"显示什么文字"、"跳转到什么页面"、"返回什么状态码"
6. test_data 必须提供具体的测试数据值，如真实手机号格式、真实姓名等
7. **测试类型(case_type)可选值**：
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
