from datetime import datetime

from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String, DateTime

db_url="mysql+pymysql://root:123456@localhost:3306/sqlalchemy_demo?charset=utf8mb4"
engine=create_engine(db_url,echo=True)

Base=declarative_base()

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


# 基于Base类创建所有模型对应的数据库表（绑定Engine）
Base.metadata.create_all(engine)

print("数据库表创建成功！")