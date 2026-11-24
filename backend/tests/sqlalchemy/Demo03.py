from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from backend.tests.sqlalchemy.Demo01 import User

db_url="mysql+pymysql://root:123456@localhost:3306/sqlalchemy_demo?charset=utf8mb4"
engine=create_engine(db_url,echo=True)
SessionFactory=sessionmaker(bind=engine)
# 什么样的对象可以使用 with .... as 来写？
# 假如一个对象里面有 __enter__() 和 __exit__() 方法，那么就可以使用 with ... as 来写
with SessionFactory() as session:
	user_all=session.query(User).all()
	print(user_all)
	print(type(user_all).__name__)
	for user in user_all:
		print(user)