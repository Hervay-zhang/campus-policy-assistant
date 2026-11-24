from backend.tests.sqlalchemy.utils.base_model import User
from backend.tests.sqlalchemy.utils.sqlalchemy_config import SessionFactory

with SessionFactory() as session:
    # 1. 排序（order_by）：对应 MySQL 的 ORDER BY
    users_asc = session.query(User).order_by(User.id).all()  # 按 id 升序（默认），对应 ORDER BY id ASC
    users_desc = session.query(User).order_by(User.id.desc()).all()  # 按 id 降序，对应 ORDER BY id DESC
    print(f'{users_asc=}')
    print(f'{users_desc=}')
    # 2. 分页（limit + offset）：对应 MySQL 的 LIMIT 和 OFFSET，适合分页查询
    # 对应 SELECT * FROM user ORDER BY id LIMIT 2 OFFSET 2
    users_page = session.query(User).order_by(User.id).limit(2).offset(2).all()
    print(f'{users_page=}')
    # 3. 统计数量（count）：对应 MySQL 的 COUNT(*)
    user_count = session.query(User).filter(User.username.like("z%")).count()
    print(f"{user_count=}")