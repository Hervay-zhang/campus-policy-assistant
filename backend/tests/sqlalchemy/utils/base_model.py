from datetime import datetime

from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime

from backend.tests.sqlalchemy.utils.sqlalchemy_config import Base


class User(Base):
    __tablename__="user"

    # 定义字段：id（主键，自增）
    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    # 定义字段：username（用户名，非空，唯一）
    username = Column(String(50), nullable=False, unique=True, comment="用户名")
    # 定义字段：password（密码，非空）
    password = Column(String(100), nullable=False, comment="密码")
    # 定义字段：create_time（创建时间，默认当前时间）
    create_time = Column(DateTime, default=datetime.now, comment="创建时间")

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, password={self.password}, create_time={self.create_time})"


class Account(Base):
    __tablename__ = 'account'

    # 账号ID
    id = Column(Integer, primary_key=True, autoincrement=True, comment="账号ID")
    # 账号
    age = Column(Integer, nullable=False, unique=True, comment="年龄")


