import re

with open(r'c:\ARGUS\cadastros\admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'@admin\.register\(TermoEncerramento\)[\s\S]*?(?=class|\Z)', '', content)

with open(r'c:\ARGUS\cadastros\admin.py', 'w', encoding='utf-8') as f:
    f.write(content)
