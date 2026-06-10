"""
数据库连接管理
使用 SQLAlchemy 2.0 异步引擎，支持连接池配置
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from config.settings import settings

# ==================== 数据库引擎 ====================

# 创建异步引擎 (支持连接池)
# 注意：使用 aiomysql 驱动，URL 前缀为 mysql+aiomysql
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 开发环境打印 SQL
    pool_size=settings.DB_POOL_SIZE,  # 连接池大小
    max_overflow=settings.DB_MAX_OVERFLOW,  # 最大溢出连接
    pool_pre_ping=True,  # 连接前检测有效性
    pool_recycle=3600,  # 连接回收时间(秒)
)

# 创建异步 Session 工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ==================== ORM 基类 ====================
# SQLAlchemy 2.0: DeclarativeBase 直接使用，不需要实例化
class Base(DeclarativeBase):
    """ORM 基类"""
    pass



# ==================== 依赖注入 ====================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话 (FastAPI 依赖注入)
    使用方式:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==================== 数据库初始化 ====================

async def init_db():
    """初始化数据库 (创建所有表)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
