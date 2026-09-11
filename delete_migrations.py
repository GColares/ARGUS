import os
import glob
import shutil

for root, dirs, files in os.walk(r'c:\ARGUS'):
    if os.path.basename(root) == 'migrations':
        for f in files:
            if f.endswith('.py') and f != '__init__.py':
                os.remove(os.path.join(root, f))
                print(f"Deleted {os.path.join(root, f)}")
        # Also remove __pycache__ if it exists
        pycache_dir = os.path.join(root, '__pycache__')
        if os.path.exists(pycache_dir):
            shutil.rmtree(pycache_dir)
            print(f"Deleted {pycache_dir}")
