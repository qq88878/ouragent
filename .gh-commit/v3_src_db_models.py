"""
数据模型 - 与 schema.sql 对应
"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, SmallInteger
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    """用户表 - 对应 schema.sql 中的 user 表"""
    __tablename__ = "user"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(64), nullable=True)
    email = Column(String(128), unique=True, nullable=True, index=True)
    phone = Column(String(32), nullable=True)
    avatar = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="STUDENT", index=True)  # STUDENT / TEACHER / ADMIN
    status = Column(SmallInteger, nullable=False, default=1)  # 1=active, 0=disabled
    last_login_time = Column(DateTime, nullable=True)
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted = Column(SmallInteger, nullable=False, default=0)  # 逻辑删除

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
