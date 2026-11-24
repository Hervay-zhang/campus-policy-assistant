from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from backend.tests.sqlalchemy.Demo01 import User

db_url="mysql+pymysql://root:123456@localhost:3306/sqlalchemy_demo?charset=utf8mb4"
engine=create_engine(db_url,echo=True)
SessionFactory=sessionmaker(bind=engine)
session=SessionFactory()
user=User(username="admin",password="123456")
session.add(user)
session.commit()
session.close()