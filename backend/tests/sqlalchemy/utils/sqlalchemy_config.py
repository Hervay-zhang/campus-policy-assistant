from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.decl_api import declarative_base
from sqlalchemy.orm.session import sessionmaker

db_url="mysql+pymysql://root:123456@localhost:3306/sqlalchemy_demo?charset=utf8mb4"
engine=create_engine(db_url,echo=True)
SessionFactory=sessionmaker(bind=engine)
session=SessionFactory()

Base=declarative_base()