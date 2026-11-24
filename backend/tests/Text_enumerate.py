from filecmp import cmp

seasons = ["Spring","Summer","Fall","Winter"]
print(list(enumerate(seasons)))
print(list(enumerate(seasons, start=1)))       # 下标从 1 开始


i=0
seq=["one","two","three"]
for element in seq:
    print (i ,seq[i])
    i +=1

seq=["one","two","three"]
for i,element in enumerate(seq):
 print(i,element)

 a = [5, 7, 6, 3, 4, 1, 2]
 b = sorted(a)
 b1 = sorted(a,reverse=True)
 print(a)
 print(b)
 print(b1)

 L = [('b', 2), ('a', 1), ('c', 3), ('d', 4)]
 a=sorted(L, key=lambda x: x[1])
 print(a)

 students = [('john', 'A', 15), ('jane', 'B', 12), ('dave', 'B', 10)]
 b=sorted(students, key=lambda s: s[2])
 b1=sorted(students, key=lambda s: s[2],reverse=True)
 print(b)
 print(b1)
    