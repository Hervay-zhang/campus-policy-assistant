import sys
from pathlib import Path

if __name__ == '__main__':
    #D:\AI20260501\pyworkspace\langchain_project\backend\scripts\check_path.py
    print(Path(__file__))
    #D:\AI20260501\pyworkspace\langchain_project\backend\scripts\check_path.py
    print(Path(__file__).resolve())
    # D:\AI20260501\pyworkspace\langchain_project\backend\scripts
    print(Path(__file__).resolve().parents[0])
    #D:\AI20260501\pyworkspace\langchain_project\backend
    print(Path(__file__).resolve().parents[1])
    BACKEND_ROOT = Path(__file__).resolve().parents[1]
    #D:\AI20260501\pyworkspace\langchain_project\backend
    print(BACKEND_ROOT)
    print(sys.path)
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))