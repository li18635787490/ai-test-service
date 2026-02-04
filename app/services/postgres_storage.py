"""
PostgreSQL 数据库存储服务 - 使用 SQLAlchemy ORM
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool

from app.config import get_settings

Base = declarative_base()


# ============ 数据库模型 ============

class RequirementAnalysisRecord(Base):
    """
    需求分析记录表 - 存储每次需求文档分析的结果
    """
    __tablename__ = 'requirement_analysis'
    __table_args__ = {'comment': '需求分析记录表 - 存储每次需求文档分析的主记录'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    document_id = Column(String(100), nullable=False, index=True, comment='文档唯一标识')
    document_name = Column(String(255), comment='文档名称')
    analysis_time = Column(DateTime, default=datetime.now, comment='分析时间')
    ai_provider = Column(String(50), comment='AI提供商(qwen/openai/anthropic)')

    # 需求统计
    total_requirements = Column(Integer, default=0, comment='需求总数')

    # 问题统计
    total_issues = Column(Integer, default=0, comment='问题总数')
    high_risk_count = Column(Integer, default=0, comment='高风险问题数量')
    medium_risk_count = Column(Integer, default=0, comment='中风险问题数量')
    low_risk_count = Column(Integer, default=0, comment='低风险问题数量')

    # 问题分类统计
    flow_break_count = Column(Integer, default=0, comment='业务流程断点数量')
    rule_unclear_count = Column(Integer, default=0, comment='规则不明确数量')
    status_unclear_count = Column(Integer, default=0, comment='状态定义不清数量')
    concurrent_missing_count = Column(Integer, default=0, comment='并发场景遗漏数量')
    reverse_flow_missing_count = Column(Integer, default=0, comment='逆向流程缺失数量')
    operation_missing_count = Column(Integer, default=0, comment='运营能力缺失数量')
    notify_missing_count = Column(Integer, default=0, comment='通知机制缺失数量')
    exception_missing_count = Column(Integer, default=0, comment='异常处理缺失数量')
    boundary_missing_count = Column(Integer, default=0, comment='边界场景遗漏数量')
    other_issue_count = Column(Integer, default=0, comment='其他问题数量')

    # 评分
    completeness_score = Column(Float, default=0, comment='完整性得分(0-100)')
    scenario_coverage_score = Column(Float, default=0, comment='场景覆盖得分(0-100)')
    description_quality_score = Column(Float, default=0, comment='描述质量得分(0-100)')
    testability_score = Column(Float, default=0, comment='可测试性得分(0-100)')
    overall_score = Column(Float, default=0, comment='综合得分(0-100)')

    # 总结
    summary = Column(Text, comment='分析总结')
    improvement_suggestions = Column(Text, comment='改进建议(JSON数组)')

    # 关联需求项
    requirements = relationship("RequirementItem", back_populates="analysis", cascade="all, delete-orphan")


class RequirementItem(Base):
    """
    需求项明细表 - 存储每个需求点的详细分析
    """
    __tablename__ = 'requirement_items'
    __table_args__ = {'comment': '需求项明细表 - 存储每个需求点的详细分析结果'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    analysis_id = Column(Integer, ForeignKey('requirement_analysis.id', ondelete='CASCADE'), nullable=False, comment='关联的分析记录ID')
    req_id = Column(String(50), comment='需求编号(如REQ-001)')
    title = Column(String(255), comment='需求标题')
    description = Column(Text, comment='需求描述')
    priority = Column(String(20), comment='优先级(高/中/低)')

    # 问题统计
    issue_count = Column(Integer, default=0, comment='该需求的问题数量')
    high_risk_count = Column(Integer, default=0, comment='高风险问题数量')
    medium_risk_count = Column(Integer, default=0, comment='中风险问题数量')
    low_risk_count = Column(Integer, default=0, comment='低风险问题数量')

    issues = Column(Text, comment='发现的问题列表(JSON数组)')
    suggestions = Column(Text, comment='改进建议列表(JSON数组)')

    analysis = relationship("RequirementAnalysisRecord", back_populates="requirements")


class TestCaseGenerationRecord(Base):
    """
    测试用例生成记录表 - 存储每次测试用例生成的结果
    """
    __tablename__ = 'testcase_generation'
    __table_args__ = {'comment': '测试用例生成记录表 - 存储每次测试用例生成的主记录'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    document_id = Column(String(100), nullable=False, index=True, comment='文档唯一标识')
    document_name = Column(String(255), comment='文档名称')
    generation_time = Column(DateTime, default=datetime.now, comment='生成时间')
    ai_provider = Column(String(50), comment='AI提供商(qwen/openai/anthropic)')

    # 用例统计
    total_cases = Column(Integer, default=0, comment='测试用例总数')

    # 按优先级统计
    p0_count = Column(Integer, default=0, comment='P0级用例数量(最高优先级)')
    p1_count = Column(Integer, default=0, comment='P1级用例数量(高优先级)')
    p2_count = Column(Integer, default=0, comment='P2级用例数量(中优先级)')
    p3_count = Column(Integer, default=0, comment='P3级用例数量(低优先级)')

    # 按类型统计
    functional_count = Column(Integer, default=0, comment='功能测试用例数量')
    boundary_count = Column(Integer, default=0, comment='边界测试用例数量')
    exception_count = Column(Integer, default=0, comment='异常测试用例数量')
    security_count = Column(Integer, default=0, comment='安全测试用例数量')
    performance_count = Column(Integer, default=0, comment='性能测试用例数量')
    compatibility_count = Column(Integer, default=0, comment='兼容性测试用例数量')
    api_count = Column(Integer, default=0, comment='接口测试用例数量')
    ui_count = Column(Integer, default=0, comment='UI测试用例数量')
    data_count = Column(Integer, default=0, comment='数据测试用例数量')
    other_count = Column(Integer, default=0, comment='其他类型用例数量')

    coverage_summary = Column(Text, comment='覆盖情况总结')

    # 关联测试用例
    test_cases = relationship("TestCaseItem", back_populates="generation", cascade="all, delete-orphan")


class TestCaseItem(Base):
    """
    测试用例明细表 - 存储每个测试用例的详细信息
    """
    __tablename__ = 'test_cases'
    __table_args__ = {'comment': '测试用例明细表 - 存储每个测试用例的详细信息'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    generation_id = Column(Integer, ForeignKey('testcase_generation.id', ondelete='CASCADE'), nullable=False, comment='关联的生成记录ID')
    case_id = Column(String(50), comment='用例编号(如TC-LOGIN-001)')
    requirement_id = Column(String(50), comment='关联的需求编号')
    title = Column(String(500), comment='用例标题')
    priority = Column(String(10), comment='优先级(P0/P1/P2/P3)')
    case_type = Column(String(50), comment='用例类型(functional/security/boundary等)')
    precondition = Column(Text, comment='前置条件')
    steps = Column(Text, comment='测试步骤(JSON数组)')
    test_data = Column(Text, comment='测试数据')
    tags = Column(Text, comment='标签(JSON数组)')

    generation = relationship("TestCaseGenerationRecord", back_populates="test_cases")


# ============ 数据库存储服务 ============

class PostgresStorage:
    """PostgreSQL 数据库存储管理器"""

    _instance = None
    _engine = None
    _SessionLocal = None
    _connected = False
    _connection_error = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._try_connect()

    def _try_connect(self):
        """尝试连接数据库"""
        if self._connected:
            return True
            
        settings = get_settings()
        
        try:
            # 创建数据库引擎
            self._engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_pre_ping=True,  # 连接前检查
                echo=False
            )
            
            # 测试连接
            from sqlalchemy import text
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # 创建会话工厂
            self._SessionLocal = sessionmaker(bind=self._engine)
            
            # 创建表
            Base.metadata.create_all(self._engine)
            
            self._connected = True
            self._connection_error = None
            print(f"[数据库] 已连接: {settings.db_host}:{settings.db_port}/{settings.db_name}")
            return True
            
        except Exception as e:
            self._connected = False
            self._connection_error = str(e)
            print(f"[数据库] 连接失败: {e}")
            print(f"[数据库] 提示: 请确保PostgreSQL已启动，并创建数据库 {settings.db_name}")
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def get_connection_error(self) -> Optional[str]:
        """获取连接错误信息"""
        return self._connection_error

    @contextmanager
    def get_session(self):
        """获取数据库会话"""
        if not self._connected:
            if not self._try_connect():
                raise Exception(f"数据库未连接: {self._connection_error}")

        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _count_issues(self, requirements: List[Dict]) -> Dict:
        """统计问题数量 - 基于AI返回的[标签]格式进行统计"""
        stats = {
            'total_issues': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'flow_break_count': 0,
            'rule_unclear_count': 0,
            'status_unclear_count': 0,
            'concurrent_missing_count': 0,
            'reverse_flow_missing_count': 0,
            'operation_missing_count': 0,
            'notify_missing_count': 0,
            'exception_missing_count': 0,
            'boundary_missing_count': 0,
            'other_issue_count': 0,
        }

        # 问题类型标签映射 - 匹配AI返回的[标签]格式
        # AI返回格式示例: "[业务流程断点] 具体描述..."
        issue_type_map = {
            'flow_break_count': ['业务流程断点', '流程断点', '用户旅程中断', '流程不闭环'],
            'rule_unclear_count': ['规则不明确', '规则不清', '计算规则', '业务规则缺失', '规则缺失'],
            'status_unclear_count': ['状态定义不清', '状态不明确', '状态流转不清'],
            'concurrent_missing_count': ['并发场景遗漏', '并发场景', '多人操作', '操作冲突'],
            'reverse_flow_missing_count': ['逆向流程缺失', '逆向流程', '退款规则', '取消规则', '退换规则', '撤销'],
            'operation_missing_count': ['运营能力缺失', '运营能力', '后台管理', '运营后台', '人工干预'],
            'notify_missing_count': ['通知机制缺失', '通知机制', '消息通知', '通知策略'],
            'exception_missing_count': ['异常处理缺失', '异常处理', '异常场景', '资金流转遗漏', '库存回滚', '售后衔接'],
            'boundary_missing_count': ['边界场景遗漏', '边界场景', '边界条件', '数据边界'],
        }

        # 高风险标签/关键词 - 涉及资金、安全、核心流程
        high_risk_tags = ['资金流转', '退款规则', '支付', '账户', '密码', '权限', '安全', '资金']
        # 低风险标签 - 建议性的改进
        low_risk_tags = ['建议', '优化建议', '可选']

        for req in requirements:
            issues = req.get('issues', [])
            for issue in issues:
                issue_text = str(issue)
                stats['total_issues'] += 1

                # 判断风险等级
                is_high_risk = any(tag in issue_text for tag in high_risk_tags)
                is_low_risk = any(tag in issue_text for tag in low_risk_tags) and not is_high_risk

                if is_high_risk:
                    stats['high_risk_count'] += 1
                elif is_low_risk:
                    stats['low_risk_count'] += 1
                else:
                    stats['medium_risk_count'] += 1

                # 匹配问题类型 - 按照关键词匹配
                matched = False
                for stat_key, keywords in issue_type_map.items():
                    if any(kw in issue_text for kw in keywords):
                        stats[stat_key] += 1
                        matched = True
                        break
                if not matched:
                    stats['other_issue_count'] += 1

        return stats

    def _count_req_issues(self, issues: List[str]) -> Dict:
        """统计单个需求的问题风险等级"""
        high_risk_tags = ['资金流转', '退款规则', '支付', '账户', '密码', '权限', '安全', '资金']
        low_risk_tags = ['建议', '优化建议', '可选']

        result = {'high': 0, 'medium': 0, 'low': 0}
        for issue in issues:
            issue_text = str(issue)
            is_high_risk = any(tag in issue_text for tag in high_risk_tags)
            is_low_risk = any(tag in issue_text for tag in low_risk_tags) and not is_high_risk

            if is_high_risk:
                result['high'] += 1
            elif is_low_risk:
                result['low'] += 1
            else:
                result['medium'] += 1
        return result

    def save_requirement_analysis(
        self,
        document_id: str,
        document_name: str,
        result: Dict[str, Any],
        ai_provider: str = None
    ) -> int:
        """保存需求分析结果"""
        with self.get_session() as session:
            # 处理需求项
            analyzed_reqs = []
            for req in result.get('analyzed_requirements', []):
                if hasattr(req, 'model_dump'):
                    req = req.model_dump()
                elif hasattr(req, 'dict'):
                    req = req.dict()
                analyzed_reqs.append(req)

            # 统计问题
            stats = self._count_issues(analyzed_reqs)

            # 创建主记录
            record = RequirementAnalysisRecord(
                document_id=document_id,
                document_name=document_name,
                ai_provider=ai_provider,
                total_requirements=result.get('total_requirements', 0),
                # 问题统计
                total_issues=stats['total_issues'],
                high_risk_count=stats['high_risk_count'],
                medium_risk_count=stats['medium_risk_count'],
                low_risk_count=stats['low_risk_count'],
                # 问题分类
                flow_break_count=stats['flow_break_count'],
                rule_unclear_count=stats['rule_unclear_count'],
                status_unclear_count=stats['status_unclear_count'],
                concurrent_missing_count=stats['concurrent_missing_count'],
                reverse_flow_missing_count=stats['reverse_flow_missing_count'],
                operation_missing_count=stats['operation_missing_count'],
                notify_missing_count=stats['notify_missing_count'],
                exception_missing_count=stats['exception_missing_count'],
                boundary_missing_count=stats['boundary_missing_count'],
                other_issue_count=stats['other_issue_count'],
                # 评分
                completeness_score=result.get('completeness_score', 0),
                scenario_coverage_score=result.get('scenario_coverage_score', 0),
                description_quality_score=result.get('description_quality_score', 0),
                testability_score=result.get('testability_score', 0),
                overall_score=result.get('overall_score', 0),
                summary=result.get('summary', ''),
                improvement_suggestions=json.dumps(result.get('improvement_suggestions', []), ensure_ascii=False)
            )
            session.add(record)
            session.flush()

            # 创建需求项明细
            for req in analyzed_reqs:
                issues = req.get('issues', [])
                issue_stats = self._count_req_issues(issues)

                item = RequirementItem(
                    analysis_id=record.id,
                    req_id=req.get('req_id', ''),
                    title=req.get('title', ''),
                    description=req.get('description', ''),
                    priority=req.get('priority'),
                    issue_count=len(issues),
                    high_risk_count=issue_stats['high'],
                    medium_risk_count=issue_stats['medium'],
                    low_risk_count=issue_stats['low'],
                    issues=json.dumps(issues, ensure_ascii=False),
                    suggestions=json.dumps(req.get('suggestions', []), ensure_ascii=False)
                )
                session.add(item)

            return record.id

    def _count_testcases(self, test_cases: List[Dict]) -> Dict:
        """统计测试用例数量"""
        stats = {
            'p0_count': 0, 'p1_count': 0, 'p2_count': 0, 'p3_count': 0,
            'functional_count': 0, 'boundary_count': 0, 'exception_count': 0,
            'security_count': 0, 'performance_count': 0, 'compatibility_count': 0,
            'api_count': 0, 'ui_count': 0, 'data_count': 0, 'other_count': 0,
        }

        for tc in test_cases:
            priority = tc.get('priority', 'P2')
            if hasattr(priority, 'value'):
                priority = priority.value
            priority = str(priority).upper()

            if priority == 'P0':
                stats['p0_count'] += 1
            elif priority == 'P1':
                stats['p1_count'] += 1
            elif priority == 'P2':
                stats['p2_count'] += 1
            else:
                stats['p3_count'] += 1

            case_type = tc.get('case_type', 'functional')
            if hasattr(case_type, 'value'):
                case_type = case_type.value
            case_type = str(case_type).lower()

            if 'functional' in case_type or 'smoke' in case_type or 'regression' in case_type:
                stats['functional_count'] += 1
            elif 'boundary' in case_type:
                stats['boundary_count'] += 1
            elif 'exception' in case_type:
                stats['exception_count'] += 1
            elif 'security' in case_type or 'sql' in case_type or 'xss' in case_type or 'auth' in case_type:
                stats['security_count'] += 1
            elif 'performance' in case_type or 'load' in case_type or 'stress' in case_type or 'concurrent' in case_type:
                stats['performance_count'] += 1
            elif 'compat' in case_type:
                stats['compatibility_count'] += 1
            elif 'api' in case_type:
                stats['api_count'] += 1
            elif 'ui' in case_type:
                stats['ui_count'] += 1
            elif 'data' in case_type:
                stats['data_count'] += 1
            else:
                stats['other_count'] += 1

        return stats

    def save_testcase_generation(
        self,
        document_id: str,
        document_name: str,
        result: Dict[str, Any],
        ai_provider: str = None
    ) -> int:
        """保存测试用例生成结果"""
        with self.get_session() as session:
            # 处理测试用例
            test_cases_data = []
            for tc in result.get('test_cases', []):
                if hasattr(tc, 'model_dump'):
                    tc = tc.model_dump()
                elif hasattr(tc, 'dict'):
                    tc = tc.dict()
                test_cases_data.append(tc)

            # 统计
            stats = self._count_testcases(test_cases_data)

            # 创建主记录
            record = TestCaseGenerationRecord(
                document_id=document_id,
                document_name=document_name,
                ai_provider=ai_provider,
                total_cases=result.get('total_cases', 0),
                # 优先级统计
                p0_count=stats['p0_count'],
                p1_count=stats['p1_count'],
                p2_count=stats['p2_count'],
                p3_count=stats['p3_count'],
                # 类型统计
                functional_count=stats['functional_count'],
                boundary_count=stats['boundary_count'],
                exception_count=stats['exception_count'],
                security_count=stats['security_count'],
                performance_count=stats['performance_count'],
                compatibility_count=stats['compatibility_count'],
                api_count=stats['api_count'],
                ui_count=stats['ui_count'],
                data_count=stats['data_count'],
                other_count=stats['other_count'],
                coverage_summary=result.get('coverage_summary', '')
            )
            session.add(record)
            session.flush()

            # 创建测试用例明细
            for tc in test_cases_data:
                priority = tc.get('priority', 'P2')
                if hasattr(priority, 'value'):
                    priority = priority.value

                case_type = tc.get('case_type', 'functional')
                if hasattr(case_type, 'value'):
                    case_type = case_type.value

                item = TestCaseItem(
                    generation_id=record.id,
                    case_id=tc.get('case_id', ''),
                    requirement_id=tc.get('requirement_id'),
                    title=tc.get('title', ''),
                    priority=str(priority),
                    case_type=str(case_type),
                    precondition=tc.get('precondition'),
                    steps=json.dumps(tc.get('steps', []), ensure_ascii=False, default=str),
                    test_data=tc.get('test_data'),
                    tags=json.dumps(tc.get('tags', []), ensure_ascii=False)
                )
                session.add(item)

            return record.id

    def get_analysis_history(
        self,
        document_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """获取需求分析历史记录"""
        with self.get_session() as session:
            query = session.query(RequirementAnalysisRecord)

            if document_id:
                query = query.filter(RequirementAnalysisRecord.document_id == document_id)

            records = query.order_by(RequirementAnalysisRecord.analysis_time.desc()).limit(limit).all()

            return [{
                'id': r.id,
                'document_id': r.document_id,
                'document_name': r.document_name,
                'analysis_time': r.analysis_time.isoformat() if r.analysis_time else None,
                'ai_provider': r.ai_provider,
                'total_requirements': r.total_requirements,
                # 问题统计
                'total_issues': r.total_issues,
                'high_risk_count': r.high_risk_count,
                'medium_risk_count': r.medium_risk_count,
                'low_risk_count': r.low_risk_count,
                # 评分
                'completeness_score': r.completeness_score,
                'scenario_coverage_score': r.scenario_coverage_score,
                'description_quality_score': r.description_quality_score,
                'testability_score': r.testability_score,
                'overall_score': r.overall_score,
                'summary': r.summary
            } for r in records]

    def get_analysis_detail(self, analysis_id: int) -> Optional[Dict]:
        """获取需求分析详情"""
        with self.get_session() as session:
            record = session.query(RequirementAnalysisRecord).filter(
                RequirementAnalysisRecord.id == analysis_id
            ).first()

            if not record:
                return None

            return {
                'id': record.id,
                'document_id': record.document_id,
                'document_name': record.document_name,
                'analysis_time': record.analysis_time.isoformat() if record.analysis_time else None,
                'ai_provider': record.ai_provider,
                'total_requirements': record.total_requirements,
                # 问题统计
                'total_issues': record.total_issues,
                'high_risk_count': record.high_risk_count,
                'medium_risk_count': record.medium_risk_count,
                'low_risk_count': record.low_risk_count,
                # 问题分类统计
                'issue_categories': {
                    'flow_break_count': record.flow_break_count,
                    'rule_unclear_count': record.rule_unclear_count,
                    'status_unclear_count': record.status_unclear_count,
                    'concurrent_missing_count': record.concurrent_missing_count,
                    'reverse_flow_missing_count': record.reverse_flow_missing_count,
                    'operation_missing_count': record.operation_missing_count,
                    'notify_missing_count': record.notify_missing_count,
                    'exception_missing_count': record.exception_missing_count,
                    'boundary_missing_count': record.boundary_missing_count,
                    'other_issue_count': record.other_issue_count,
                },
                # 评分
                'completeness_score': record.completeness_score,
                'scenario_coverage_score': record.scenario_coverage_score,
                'description_quality_score': record.description_quality_score,
                'testability_score': record.testability_score,
                'overall_score': record.overall_score,
                'summary': record.summary,
                'improvement_suggestions': json.loads(record.improvement_suggestions or '[]'),
                # 需求项明细
                'requirements': [{
                    'req_id': item.req_id,
                    'title': item.title,
                    'description': item.description,
                    'priority': item.priority,
                    'issue_count': item.issue_count,
                    'high_risk_count': item.high_risk_count,
                    'medium_risk_count': item.medium_risk_count,
                    'low_risk_count': item.low_risk_count,
                    'issues': json.loads(item.issues or '[]'),
                    'suggestions': json.loads(item.suggestions or '[]')
                } for item in record.requirements]
            }

    def get_testcase_history(
        self,
        document_id: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """获取测试用例生成历史"""
        with self.get_session() as session:
            query = session.query(TestCaseGenerationRecord)

            if document_id:
                query = query.filter(TestCaseGenerationRecord.document_id == document_id)

            records = query.order_by(TestCaseGenerationRecord.generation_time.desc()).limit(limit).all()

            return [{
                'id': r.id,
                'document_id': r.document_id,
                'document_name': r.document_name,
                'generation_time': r.generation_time.isoformat() if r.generation_time else None,
                'ai_provider': r.ai_provider,
                'total_cases': r.total_cases,
                # 优先级统计
                'p0_count': r.p0_count,
                'p1_count': r.p1_count,
                'p2_count': r.p2_count,
                'p3_count': r.p3_count,
                'coverage_summary': r.coverage_summary
            } for r in records]

    def get_testcase_detail(self, generation_id: int) -> Optional[Dict]:
        """获取测试用例生成详情"""
        with self.get_session() as session:
            record = session.query(TestCaseGenerationRecord).filter(
                TestCaseGenerationRecord.id == generation_id
            ).first()

            if not record:
                return None

            return {
                'id': record.id,
                'document_id': record.document_id,
                'document_name': record.document_name,
                'generation_time': record.generation_time.isoformat() if record.generation_time else None,
                'ai_provider': record.ai_provider,
                'total_cases': record.total_cases,
                # 优先级统计
                'priority_stats': {
                    'p0_count': record.p0_count,
                    'p1_count': record.p1_count,
                    'p2_count': record.p2_count,
                    'p3_count': record.p3_count,
                },
                # 类型统计
                'type_stats': {
                    'functional_count': record.functional_count,
                    'boundary_count': record.boundary_count,
                    'exception_count': record.exception_count,
                    'security_count': record.security_count,
                    'performance_count': record.performance_count,
                    'compatibility_count': record.compatibility_count,
                    'api_count': record.api_count,
                    'ui_count': record.ui_count,
                    'data_count': record.data_count,
                    'other_count': record.other_count,
                },
                'coverage_summary': record.coverage_summary,
                'test_cases': [{
                    'case_id': tc.case_id,
                    'requirement_id': tc.requirement_id,
                    'title': tc.title,
                    'priority': tc.priority,
                    'case_type': tc.case_type,
                    'precondition': tc.precondition,
                    'steps': json.loads(tc.steps or '[]'),
                    'test_data': tc.test_data,
                    'tags': json.loads(tc.tags or '[]')
                } for tc in record.test_cases]
            }

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_session() as session:
            from sqlalchemy import func

            # 分析次数
            analysis_count = session.query(func.count(RequirementAnalysisRecord.id)).scalar() or 0

            # 测试用例生成次数
            testcase_gen_count = session.query(func.count(TestCaseGenerationRecord.id)).scalar() or 0

            # 平均分
            avg_score = session.query(func.avg(RequirementAnalysisRecord.overall_score)).scalar() or 0

            # 总测试用例数
            total_cases = session.query(func.sum(TestCaseGenerationRecord.total_cases)).scalar() or 0

            return {
                'total_analysis_count': analysis_count,
                'total_testcase_generations': testcase_gen_count,
                'average_score': round(float(avg_score), 1),
                'total_test_cases': int(total_cases),
                'database_type': 'postgresql'
            }

    def delete_analysis(self, analysis_id: int) -> bool:
        """删除需求分析记录"""
        with self.get_session() as session:
            record = session.query(RequirementAnalysisRecord).filter(
                RequirementAnalysisRecord.id == analysis_id
            ).first()

            if record:
                session.delete(record)
                return True
            return False

    def delete_testcase(self, generation_id: int) -> bool:
        """删除测试用例生成记录"""
        with self.get_session() as session:
            record = session.query(TestCaseGenerationRecord).filter(
                TestCaseGenerationRecord.id == generation_id
            ).first()

            if record:
                session.delete(record)
                return True
            return False
