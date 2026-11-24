import asyncio

#假如我定义了一个异步函数，在另一个异步函数中调用，没有使用 await, 那么它是什么？
async def testAwait():
	print("我是谁")
async def main():
	a=testAwait()
	# a 不是testAwait的返回值，是一个协程对象
	print(a)
	print(type(a).__name__)
	print("是否是coroutine对象:", asyncio.iscoroutine(a))
	await a


if __name__ == '__main__':
	asyncio.run(main())