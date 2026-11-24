import enum
from enum import Enum


class Status(Enum):
    ENABLE =  1
    DISABLE = 2
    PENDING = 3

s=Status.ENABLE
# s 其实就是Status类的对象
print(s)
print(type(s).__name__)
print(s.name)
print(s.value)

s1 = Status(2)
print(s1)

s2 = Status["ENABLE"]
print(s2)

for status in Status:
    print(status)


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    ready = "ready"
    failed = "failed"

class DocumentStatus2(enum.Enum):
    pending = "pending"
    ready = "ready"
    failed = "failed"

print(DocumentStatus.pending=="pending")
print(DocumentStatus2.pending.value=="pending")