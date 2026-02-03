from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class AIProvider(str, Enum):
    """支持的 AI 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"


class DocumentType(str, Enum):
    """支持的文档类型"""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"


class CheckDimension(str, Enum):
    """检测维度"""
    FORMAT = "format"           # 格式规范
    CONTENT = "content"         # 内容质量
    LOGIC = "logic"             # 逻辑一致性
    SENSITIVE = "sensitive"     # 敏感信息
    COMPLIANCE = "compliance"   # 合规检查
    # 需求文档专用维度
    REQ_COMPLETENESS = "req_completeness"   # 需求完整性
    REQ_SCENARIO = "req_scenario"           # 场景覆盖
    REQ_DESCRIPTION = "req_description"     # 描述清晰度
    REQ_TESTABILITY = "req_testability"     # 可测试性


class TestCasePriority(str, Enum):
    """测试用例优先级"""
    P0 = "P0"  # 最高优先级，核心功能
    P1 = "P1"  # 高优先级，重要功能
    P2 = "P2"  # 中优先级，一般功能
    P3 = "P3"  # 低优先级，边缘功能


class TestCaseType(str, Enum):
    """测试用例类型"""
    FUNCTIONAL = "functional"       # 功能测试
    BOUNDARY = "boundary"           # 边界测试
    EXCEPTION = "exception"         # 异常测试
    PERFORMANCE = "performance"     # 性能测试
    SECURITY = "security"           # 安全测试
    COMPATIBILITY = "compatibility" # 兼容性测试
    USABILITY = "usability"         # 易用性测试
    API = "api"                     # 接口测试
    UI = "ui"                       # UI测试
    DATA = "data"                   # 数据测试
    REGRESSION = "regression"       # 回归测试
    SMOKE = "smoke"                 # 冒烟测试
    INTEGRATION = "integration"     # 集成测试
    # 新增测试类型
    SQL_INJECTION = "sql_injection"             # SQL注入测试
    XSS = "xss"                                 # XSS跨站脚本测试
    CSRF = "csrf"                              # CSRF跨站请求伪造测试
    AUTH = "auth"                              # 认证授权测试
    PERMISSION = "permission"                   # 权限测试
    SENSITIVE_DATA = "sensitive_data"           # 敏感数据测试
    MOBILE_COMPAT = "mobile_compat"             # 移动端兼容性测试
    BROWSER_COMPAT = "browser_compat"           # 浏览器兼容性测试
    RESOLUTION_COMPAT = "resolution_compat"     # 分辨率兼容性测试
    API_CONTRACT = "api_contract"               # 接口契约测试
    API_SECURITY = "api_security"               # 接口安全测试
    API_PERFORMANCE = "api_performance"         # 接口性能测试
    UI_INTERACTION = "ui_interaction"           # UI交互测试
    UI_RESPONSIVE = "ui_responsive"             # UI响应式测试
    UI_ACCESSIBILITY = "ui_accessibility"       # UI无障碍测试
    LOAD = "load"                              # 负载测试
    STRESS = "stress"                          # 压力测试
    CONCURRENT = "concurrent"                   # 并发测试
    RELIABILITY = "reliability"                 # 可靠性测试
    RECOVERY = "recovery"                       # 恢复性测试
    UPGRADE = "upgrade"                         # 升级测试
    LOCALIZATION = "localization"               # 本地化测试
    DATABASE = "database"                       # 数据库测试
    CACHE = "cache"                            # 缓存测试
    LOG = "log"                                # 日志测试
    MONITOR = "monitor"                         # 监控告警测试


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ============ Request Models ============

class CheckRequest(BaseModel):
    """检测请求"""
    document_id: str = Field(..., description="文档ID")
    dimensions: List[CheckDimension] = Field(
        default=[CheckDimension.FORMAT, CheckDimension.CONTENT],
        description="检测维度"
    )
    ai_provider: Optional[AIProvider] = Field(
        default=None,
        description="AI 提供商，不指定则使用默认"
    )
    custom_rules: Optional[str] = Field(
        default=None,
        description="自定义检测规则描述"
    )


# ============ Response Models ============

class Issue(BaseModel):
    """检测发现的问题"""
    dimension: CheckDimension
    severity: Severity
    location: Optional[str] = Field(default=None, description="问题位置")
    description: str = Field(..., description="问题描述")
    suggestion: Optional[str] = Field(default=None, description="修改建议")


class CheckResult(BaseModel):
    """检测结果"""
    dimension: CheckDimension
    score: float = Field(..., ge=0, le=100, description="评分 0-100")
    summary: str = Field(..., description="检测总结")
    issues: List[Issue] = Field(default=[], description="发现的问题")


class DocumentInfo(BaseModel):
    """文档信息"""
    id: str
    filename: str
    file_type: DocumentType
    file_size: int
    page_count: Optional[int] = None
    upload_time: datetime


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: TaskStatus
    document: DocumentInfo
    progress: int = Field(default=0, ge=0, le=100)
    results: Optional[List[CheckResult]] = None
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ReportResponse(BaseModel):
    """报告响应"""
    task_id: str
    document: DocumentInfo
    overall_score: float
    summary: str
    results: List[CheckResult]
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    generated_at: datetime


# ============ 测试用例相关模型 ============

class TestStep(BaseModel):
    """测试步骤"""
    step_number: int = Field(..., description="步骤序号")
    action: str = Field(..., description="操作描述")
    expected_result: str = Field(..., description="预期结果")


class TestCase(BaseModel):
    """测试用例"""
    case_id: str = Field(..., description="用例编号")
    requirement_id: Optional[str] = Field(default=None, description="关联需求ID")
    title: str = Field(..., description="用例标题")
    priority: TestCasePriority = Field(..., description="优先级")
    case_type: TestCaseType = Field(..., description="用例类型")
    precondition: Optional[str] = Field(default=None, description="前置条件")
    steps: List[TestStep] = Field(..., description="测试步骤")
    test_data: Optional[str] = Field(default=None, description="测试数据")
    tags: List[str] = Field(default=[], description="标签")


class RequirementItem(BaseModel):
    """需求项"""
    req_id: str = Field(..., description="需求ID")
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="需求描述")
    priority: Optional[str] = Field(default=None, description="优先级")
    issues: List[str] = Field(default=[], description="发现的问题")
    suggestions: List[str] = Field(default=[], description="改进建议")


class RequirementAnalysisResult(BaseModel):
    """需求分析结果"""
    total_requirements: int = Field(..., description="需求总数")
    analyzed_requirements: List[RequirementItem] = Field(..., description="分析的需求项")
    completeness_score: float = Field(..., description="完整性得分")
    scenario_coverage_score: float = Field(..., description="场景覆盖得分")
    description_quality_score: float = Field(..., description="描述质量得分")
    testability_score: float = Field(..., description="可测试性得分")
    overall_score: float = Field(..., description="综合得分")
    summary: str = Field(..., description="分析总结")
    improvement_suggestions: List[str] = Field(..., description="改进建议")


class TestCaseGenerationResult(BaseModel):
    """测试用例生成结果"""
    document_id: str
    total_cases: int = Field(..., description="生成的用例总数")
    test_cases: List[TestCase] = Field(..., description="测试用例列表")
    coverage_summary: str = Field(..., description="覆盖情况总结")
    generated_at: datetime

