from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm.session import sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
	pass

settings=get_settings()
engine=create_engine(
	settings.database_url,
	echo=settings.debug,
	pool_pre_ping=True # 使用连接前检查连接是否还可用,如果池子中的连接可用，就直接使用
)

SessionLocal=sessionmaker(
	bind=engine,
	expire_on_commit=False,
)

# 执行这个函数，其实就是拿到了一个关于session的生成器对象
def get_session():
	with SessionLocal() as session:
		yield session


def init_database():
	#作用是SQLAlchemy 看到 models.py
	from app import models  # noqa
	Base.metadata.create_all(engine)

