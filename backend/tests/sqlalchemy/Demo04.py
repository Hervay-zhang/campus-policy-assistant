from backend.tests.sqlalchemy.utils.base_model import User
from backend.tests.sqlalchemy.utils.sqlalchemy_config import SessionFactory

with SessionFactory() as session:
	# 1. 查询所有数据（返回列表，对应 MySQL 的 SELECT * FROM user）
	user_all = session.query(User).all()
	for user in user_all:
		print(user)

	# 2. 查询单条数据（根据主键，对应 MySQL 的 SELECT * FROM user WHERE id = 1，不存在则返回None）
	user_by_id=session.get(User,1)
	print(user_by_id)

	# 3. 查询单条数据（不存在则返回 None，对应 MySQL 的 SELECT * FROM user  LIMIT 1）
	user_first=session.query(User).first()


	# 4. 查指定字段数据
	# 默认.query(User)会查询User的所有字段 可以使用User.字段控制查询字段
	users=session.query(User.username,User.password).all()
	for tup in users:
		print(tup)
		print(tup[0])
		print(tup[1])