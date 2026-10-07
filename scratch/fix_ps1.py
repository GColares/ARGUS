import re

with open('scratch/build_dashboards_native.ps1', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix $(var): to $($var):
fixed = re.sub(r'\$\(([a-zA-Z0-9_]+)\):', r'$($\1):', content)

with open('scratch/build_dashboards_native.ps1', 'w', encoding='utf-8') as f:
    f.write(fixed)

print('Fixed $(var) to $($var)')
