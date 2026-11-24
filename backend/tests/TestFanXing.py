from typing import List

# 泛型约束变量
list:List[int]=[1,2,3,4]
list.append(5)
#list.append("abc")

print(list)

# 泛型列表
def first_item(items: list[int]):
    return items[0]

print(first_item([1,2,3]))     # 推断 int
print(first_item(["a","b"]))   # 推断 str
from typing import TypeVar
NumStr=TypeVar("NumStr",int,str)

a:NumStr=1
b:NumStr="abc"
c:NumStr=['a','b']

#此时这个T 是任意类型
T=TypeVar("T")
d:T=['a','b']

def first_item2(items:List[T])->T:
    return items[0]

print(first_item2([1,2,3]))

