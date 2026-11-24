# time.perf_counter() Python 高精度性能计时器。


import time

start = time.perf_counter()
time.sleep(3)
elapsed=time.perf_counter()-start
print(f"耗时 {elapsed:.4f} 秒")