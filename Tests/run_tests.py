""" 
Run all files starting with 'test_' in the Tests folder.
"""

import os
import sys

cwd = os.getcwd()
print(f"Current working directory: {cwd}")
# Whether we are at not at 'Tests' folder or we are
at_root = not cwd.endswith("Tests")
if not at_root:
    files = os.listdir()
    files = [f for f in files if f.startswith("test_") and f.endswith(".py")]
else:
    files = os.listdir("Tests")
    files = [f"Tests/{f}" for f in files if f.startswith("test_") and f.endswith(".py")]
print(f"Files in directory: {files}")

for f in files:
    print(f"Running {f}")
    os.system(f"python {f}")
    print(f"Finished {f}")