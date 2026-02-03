"""
测试数据生成器 - 使用Faker生成真实多样的测试数据
"""
from faker import Faker
from typing import Dict, List, Optional, Any
import random
import json

# 创建中文Faker实例
fake = Faker('zh_CN')
fake_en = Faker('en_US')


class TestDataGenerator:
    """测试数据生成器"""

    # 常见字段类型映射
    FIELD_PATTERNS = {
        # 用户相关
        'username': lambda: fake.user_name(),
        'user_name': lambda: fake.user_name(),
        'name': lambda: fake.name(),
        'real_name': lambda: fake.name(),
        'nickname': lambda: fake.name()[:4] + str(random.randint(100, 999)),
        'email': lambda: fake.email(),
        'phone': lambda: fake.phone_number(),
        'mobile': lambda: fake.phone_number(),
        'telephone': lambda: fake.phone_number(),
        'password': lambda: f"Test@{random.randint(100000, 999999)}",
        'id_card': lambda: fake.ssn(),
        'address': lambda: fake.address(),
        'city': lambda: fake.city(),
        'province': lambda: fake.province(),

        # 商品相关
        'product_name': lambda: fake.word() + random.choice(['手机', '电脑', '耳机', '键盘', '鼠标', '显示器']),
        'sku': lambda: f"SKU{random.randint(10000000, 99999999)}",
        'price': lambda: round(random.uniform(9.9, 9999.99), 2),
        'amount': lambda: round(random.uniform(0.01, 99999.99), 2),
        'quantity': lambda: random.randint(1, 100),
        'stock': lambda: random.randint(0, 10000),

        # 订单相关
        'order_no': lambda: f"ORD{fake.date_time_this_year().strftime('%Y%m%d')}{random.randint(100000, 999999)}",
        'order_id': lambda: f"ORD{random.randint(1000000000, 9999999999)}",
        'trade_no': lambda: f"T{fake.date_time_this_year().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",

        # 时间相关
        'date': lambda: fake.date(),
        'datetime': lambda: fake.date_time().strftime('%Y-%m-%d %H:%M:%S'),
        'time': lambda: fake.time(),
        'timestamp': lambda: int(fake.date_time().timestamp()),
        'create_time': lambda: fake.date_time_this_year().strftime('%Y-%m-%d %H:%M:%S'),
        'update_time': lambda: fake.date_time_this_year().strftime('%Y-%m-%d %H:%M:%S'),

        # 文本相关
        'title': lambda: fake.sentence()[:20],
        'description': lambda: fake.text(max_nb_chars=100),
        'content': lambda: fake.text(max_nb_chars=200),
        'remark': lambda: fake.sentence(),
        'comment': lambda: random.choice(['很好', '不错', '一般', '还行', '满意', '推荐购买']),

        # 状态相关
        'status': lambda: random.choice([0, 1, 2, 3]),
        'state': lambda: random.choice(['pending', 'processing', 'completed', 'cancelled']),
        'type': lambda: random.randint(1, 5),

        # ID相关
        'id': lambda: random.randint(1, 999999),
        'user_id': lambda: random.randint(10000, 99999),
        'product_id': lambda: random.randint(10000, 99999),

        # 其他
        'ip': lambda: fake.ipv4(),
        'url': lambda: fake.url(),
        'image': lambda: f"https://example.com/images/{random.randint(1, 1000)}.jpg",
        'code': lambda: f"{random.randint(100000, 999999)}",
        'verify_code': lambda: f"{random.randint(1000, 9999)}",
    }

    # 边界值生成器
    BOUNDARY_VALUES = {
        'string': {
            'empty': '',
            'single': 'a',
            'normal': lambda: fake.word(),
            'long': lambda: 'a' * 256,
            'very_long': lambda: 'a' * 1001,
            'special': '!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\',
            'chinese': '测试中文字符串',
            'mixed': 'Test测试123!@#',
            'space': '   ',
            'newline': 'line1\nline2',
            'sql_injection': "'; DROP TABLE users; --",
            'xss': '<script>alert("xss")</script>',
        },
        'number': {
            'zero': 0,
            'negative': -1,
            'min': -2147483648,
            'max': 2147483647,
            'float': 3.14159,
            'small_float': 0.001,
            'large': 999999999,
        },
        'amount': {
            'zero': 0.00,
            'penny': 0.01,
            'normal': lambda: round(random.uniform(10, 1000), 2),
            'large': 99999999.99,
            'negative': -100.00,
            'many_decimals': 100.123456,
        },
        'date': {
            'past': lambda: fake.date_between(start_date='-10y', end_date='-1d'),
            'future': lambda: fake.date_between(start_date='+1d', end_date='+1y'),
            'today': lambda: fake.date_object(),
            'edge_year': '1970-01-01',
            'far_future': '2099-12-31',
        },
        'array': {
            'empty': [],
            'single': lambda: [random.randint(1, 100)],
            'normal': lambda: [random.randint(1, 100) for _ in range(5)],
            'large': lambda: list(range(1000)),
        }
    }

    @classmethod
    def generate_for_field(cls, field_name: str, field_type: str = None) -> Any:
        """根据字段名生成测试数据"""
        field_lower = field_name.lower()

        # 精确匹配
        if field_lower in cls.FIELD_PATTERNS:
            return cls.FIELD_PATTERNS[field_lower]()

        # 模糊匹配
        for pattern, generator in cls.FIELD_PATTERNS.items():
            if pattern in field_lower or field_lower in pattern:
                return generator()

        # 根据字段类型
        if field_type:
            if field_type in ('string', 'str', 'varchar', 'text'):
                return fake.word()
            elif field_type in ('int', 'integer', 'number'):
                return random.randint(1, 1000)
            elif field_type in ('float', 'double', 'decimal'):
                return round(random.uniform(0, 1000), 2)
            elif field_type in ('bool', 'boolean'):
                return random.choice([True, False])
            elif field_type in ('date', 'datetime'):
                return fake.date()

        # 默认返回随机字符串
        return fake.word()

    @classmethod
    def generate_boundary_data(cls, field_name: str, data_type: str = 'string') -> Dict[str, Any]:
        """生成边界测试数据"""
        if data_type not in cls.BOUNDARY_VALUES:
            data_type = 'string'

        result = {}
        for key, value in cls.BOUNDARY_VALUES[data_type].items():
            if callable(value):
                result[key] = value()
            else:
                result[key] = value

        return result

    @classmethod
    def generate_test_dataset(cls, fields: List[Dict], count: int = 5) -> List[Dict]:
        """生成测试数据集

        Args:
            fields: 字段定义列表，如 [{"name": "username", "type": "string"}, ...]
            count: 生成的数据条数

        Returns:
            测试数据列表
        """
        dataset = []
        for _ in range(count):
            record = {}
            for field in fields:
                field_name = field.get('name', '')
                field_type = field.get('type', 'string')
                record[field_name] = cls.generate_for_field(field_name, field_type)
            dataset.append(record)
        return dataset

    @classmethod
    def generate_for_scenario(cls, scenario: str) -> Dict[str, Any]:
        """根据场景生成测试数据"""
        scenarios = {
            '用户注册': {
                'username': cls.FIELD_PATTERNS['username'](),
                'password': cls.FIELD_PATTERNS['password'](),
                'email': cls.FIELD_PATTERNS['email'](),
                'phone': cls.FIELD_PATTERNS['phone'](),
                'verify_code': cls.FIELD_PATTERNS['verify_code'](),
            },
            '用户登录': {
                'username': cls.FIELD_PATTERNS['username'](),
                'password': cls.FIELD_PATTERNS['password'](),
            },
            '下单': {
                'user_id': cls.FIELD_PATTERNS['user_id'](),
                'product_id': cls.FIELD_PATTERNS['product_id'](),
                'quantity': cls.FIELD_PATTERNS['quantity'](),
                'address': cls.FIELD_PATTERNS['address'](),
                'phone': cls.FIELD_PATTERNS['phone'](),
                'remark': cls.FIELD_PATTERNS['remark'](),
            },
            '支付': {
                'order_no': cls.FIELD_PATTERNS['order_no'](),
                'amount': cls.FIELD_PATTERNS['amount'](),
                'pay_type': random.choice(['alipay', 'wechat', 'bank_card']),
            },
            '搜索': {
                'keyword': fake.word(),
                'category': random.randint(1, 10),
                'min_price': round(random.uniform(0, 100), 2),
                'max_price': round(random.uniform(100, 10000), 2),
                'page': 1,
                'page_size': 20,
            },
        }

        # 尝试匹配场景
        for key, data in scenarios.items():
            if key in scenario:
                return data

        # 默认返回通用数据
        return {
            'id': cls.FIELD_PATTERNS['id'](),
            'name': cls.FIELD_PATTERNS['name'](),
            'value': fake.word(),
        }

    @classmethod
    def format_test_data(cls, data: Dict, format_type: str = 'json') -> str:
        """格式化测试数据"""
        if format_type == 'json':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'table':
            lines = []
            for key, value in data.items():
                lines.append(f"| {key} | {value} |")
            return "\n".join(lines)
        elif format_type == 'text':
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        else:
            return str(data)


# 便捷函数
def generate_test_data(field_name: str, field_type: str = None) -> Any:
    """生成单个字段的测试数据"""
    return TestDataGenerator.generate_for_field(field_name, field_type)


def generate_boundary_data(field_name: str, data_type: str = 'string') -> Dict:
    """生成边界测试数据"""
    return TestDataGenerator.generate_boundary_data(field_name, data_type)


def generate_scenario_data(scenario: str) -> Dict:
    """生成场景测试数据"""
    return TestDataGenerator.generate_for_scenario(scenario)
