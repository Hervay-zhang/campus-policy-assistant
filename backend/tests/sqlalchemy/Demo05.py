from backend.tests.sqlalchemy.utils.base_model import User
from backend.tests.sqlalchemy.utils.sqlalchemy_config import SessionFactory

with SessionFactory() as session:
	# 1. 等于（==），对应 MySQL 的 WHERE username = 'zhangsan'
	user1=session.query(User).filter(User.username=="admin").first()
	print(f"{user1=}")
	# 2. 不等于（!=），对应 MySQL 的 WHERE username != 'zhangsan'
	user2 = session.query(User).filter(User.username != "admin").first()
	print(f"{user2=}")
	# 3. 模糊查询（like），对应 MySQL 的 WHERE username LIKE '%a%'
	users3 = session.query(User).filter(User.username.like("%a%")).all()
	print(f"{users3=}")
	# 4. 范围查询（in_），对应 MySQL 的 WHERE id IN (1,2,3)
	users4 = session.query(User).filter(User.id.in_([1,2,3])).all()
	print(f"{users4=}")

	# 5. 大于（>）、小于（<）、大于等于（>=）、小于等于（<=）
	users5 = session.query(User).filter(User.id >= 1).all()
	print(f"{users5=}")

	# 6. 多条件查询（and_ / or_），对应 MySQL 的 AND / OR
	from sqlalchemy import and_, or_

	# 对应 WHERE id > 1 AND username LIKE 'w%'
	users6 = session.query(User).filter(and_(User.id >1, User.username.like("w%"))).all()
	print(f"{users6=}")

	# 对应 WHERE username='zhangsan' AND password='123456'
	users7 = session.query(User).filter(and_(User.password=="123456", User.username=="admin")).all()
	print(f"{users7=}")

	# 对应 WHERE id = 1 OR username LIKE 'w%'
	users8 = session.query(User).filter(or_(User.id==1, User.username.like("w%"))).all()
	print(f"{users8=}")
