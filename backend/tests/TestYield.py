def count(n):
	for i in range(n):
		yield i

print(count(5))
gen=count(5)
# 通过循环读取
# for i in gen:
# 	print(i)

# 可以通过next 获取里面的值
print(next(gen))
print(next(gen))