list01=[1,2,3,4]
print(*list01)
print(list01)

def add(a,b,c,d):
    return a+b+c+d

print(add(list01[0],list01[1],list01[2],list01[3]))
print(add(*list01))

dict01={"name2":"xiaowang","age":20}
def show(name2, age):
    print(name2, age)
show(dict01['name2'],dict01['age'])
show(**dict01)