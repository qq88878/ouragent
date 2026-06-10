"""
数据库初始化脚本
"""

import asyncio
from sqlalchemy import text

from .database import engine, init_db


async def init_database():
    """初始化数据库"""
    print("🗄️  正在初始化数据库...")

    # 创建所有表
    await init_db()

    # 执行自定义初始化 (可选)
    async with engine.begin() as conn:
        # 创建索引 (与 schema.sql 一致)
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_username ON user(username);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_role ON user(role);
        """))

    print("✅ 数据库初始化完成")


if __name__ == "__main__":
    asyncio.run(init_database())

