#解决导入的backend为模型的错误
import sys
from pathlib import Path
# parent.parent.parent 往上跳三层：scripts → backend → langchain_project
root_path = str(Path(__file__).parent.parent)
sys.path.append(root_path)

from app.database import init_database

def main():
    init_database()
    print("数据库初始化完成")

if __name__ == '__main__':

    main()