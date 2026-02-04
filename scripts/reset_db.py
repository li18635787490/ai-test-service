"""
数据库初始化/重置脚本
运行方式: python scripts/reset_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.postgres_storage import Base
from app.config import get_settings
from sqlalchemy import create_engine, text

def reset_database():
    """删除并重新创建所有表"""
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    print(f"连接数据库: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    
    # 删除旧表
    with engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS test_cases CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS testcase_generation CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS requirement_items CASCADE'))
        conn.execute(text('DROP TABLE IF EXISTS requirement_analysis CASCADE'))
        conn.commit()
    print("已删除旧表")
    
    # 重新创建表
    Base.metadata.create_all(engine)
    print("已创建新表")
    
    print("\n表结构更新完成！")
    print("\n创建的表:")
    print("  - requirement_analysis (需求分析记录表)")
    print("  - requirement_items (需求项明细表)")
    print("  - testcase_generation (测试用例生成记录表)")
    print("  - test_cases (测试用例明细表)")

if __name__ == "__main__":
    reset_database()
