import re

with open(r'c:\ARGUS\cadastros\urls.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
imported = False

for line in lines:
    if "from django.views.generic.base import RedirectView" in line:
        continue
    new_lines.append(line)

new_content = "from django.views.generic.base import RedirectView\n" + "".join(new_lines)

with open(r'c:\ARGUS\cadastros\urls.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
