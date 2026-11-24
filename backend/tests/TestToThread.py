import asyncio
import time

# 阻塞的同步函数
def blocking_work(x: int):
    time.sleep(2)   # 会阻塞线程的sleep
    return x * 10

async def main():
    # 将阻塞函数放到线程执行，await等待线程完成
    res = await asyncio.to_thread(blocking_work, 5)
    print(res)

asyncio.run(main())


list1=[1,2,3,4]
print(*list1)



import asyncio
import time

def heavy_task(n):
    time.sleep(1)
    return n**2

async def main():
    tasks = [
        asyncio.to_thread(heavy_task, i)
        for i in range(5)
    ]
    results = await asyncio.gather(*tasks)
    print(results)

asyncio.run(main())