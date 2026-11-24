from backend.tests.sqlalchemy.utils.sqlalchemy_config import engine, Base

if __name__ == '__main__':
    # # noqa 消除未使用警告
    from backend.tests.sqlalchemy.utils.base_model import Account # noqa
    Base.metadata.create_all(engine)