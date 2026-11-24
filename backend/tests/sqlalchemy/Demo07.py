
from sqlalchemy import select

from sqlalchemy.sql.functions import func

from backend.tests.sqlalchemy.utils.base_model import Account
from backend.tests.sqlalchemy.utils.sqlalchemy_config import SessionFactory

with (SessionFactory() as session):
    # 1.简单分组查询
    # 因为聚合函数是数据库提供的函数 所以需要导入func
    # 默认query(Account)查询所有列 聚合查询只能查询分组列与聚合函数所以
    # 所以需要查询指定列
    # select age,count(id) from account group by age
    group1=session.query(Account.age,func.count(Account.id)).group_by(Account.age).all()
    print(group1)
    # 聚合比较特殊 不会返回对应的对象 所以默认以元组返回
    # 如果想以字典形式返回需要使用新版2.0 API然后使用.mappings()
    # statement
    stmt = select(
        Account.age,
        func.count(Account.id).label("count")
    ).group_by(Account.age)
    # dict --> map
    group2 = session.execute(stmt).mappings().all()
    print(group2)

    # 2.having分组筛选
    # 可以直接使用having()进行分组的筛选
	# select age,count(id) from account group by age having count(id)>1
    group3 = session.query(Account.age, func.count(Account.id)).group_by(Account.age).having(func.count(Account.id)>1).all()
    print(group3)
    stmt = select(
        Account.age,
        func.count(Account.id).label("count")
    ).group_by(Account.age).having(func.count(Account.id)>1)
    group4 = session.execute(stmt).mappings().all()
    print(group4)