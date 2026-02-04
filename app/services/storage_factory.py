"""
存储服务工厂 - PostgreSQL 数据库存储
"""
from app.services.postgres_storage import PostgresStorage

_storage_instance = None


def get_storage() -> PostgresStorage:
    """获取PostgreSQL存储实例（必须连接成功）"""
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = PostgresStorage()

    # 检查数据库连接状态
    if not _storage_instance.is_connected():
        error_msg = _storage_instance.get_connection_error() or "未知错误"
        raise Exception(f"数据库连接失败: {error_msg}。请检查 .env 配置文件中的数据库配置。")

    return _storage_instance


def reset_storage():
    """重置存储实例"""
    global _storage_instance
    _storage_instance = None
