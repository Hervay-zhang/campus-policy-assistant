raw_str = '["qwen-turbo","qwen-plus","deepseek"]'
print(type(raw_str))

print("-"*80)

import json
raw_str = '["qwen-turbo","qwen-plus","deepseek"]'
result = json.loads(raw_str)
print(result)
# ['qwen-turbo', 'qwen-plus', 'deepseek']
print(type(result))
# <class 'list'>

print("-"*80)

import ast
raw_str = '["qwen-turbo","qwen-plus","deepseek"]'
result = ast.literal_eval(raw_str)
print(result)
# ['qwen-turbo', 'qwen-plus', 'deepseek']

print("-"*80)
raw_str = '["qwen-turbo","qwen-plus","deepseek"]'
print(list(raw_str))
# print(raw_str)
# ['[', '"', 'q', 'w', 'e', 'n', '-', 't', 'u', 'r', 'b', 'o', '"', ',', ...]