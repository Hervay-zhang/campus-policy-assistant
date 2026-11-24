import sys
print(sys.executable)    # 打印当前正在使用的python.exe路径，必须是D盘.venv下面，绝对不能C:\Python314
print(sys.version)       # 确认版本3.10

import faulthandler
faulthandler.enable()
print("hello world")

import asyncio

async def fn():
    print("async ok")

async def main():
    co = fn()
    print(repr(co))

if __name__ == "__main__":
    asyncio.run(main())