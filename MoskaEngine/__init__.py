"""
In this __init__.py file, we will set-up paths, to allow imports between folders of this library.
Namely, we will add this folder to the path, so that we can import from the parent folder.

We will also define a constant, which is the path to the root folder of this library.
"""
import os
import sys
def __initialize_pkg__():
    # Add the parent folder to the path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    # Define the path to the root folder of this library
    MOSKA_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    os.environ["MOSKA_ROOT_PATH"] = MOSKA_ROOT_PATH
    print("MOSKA_ROOT_PATH:", MOSKA_ROOT_PATH)

__initialize_pkg__()