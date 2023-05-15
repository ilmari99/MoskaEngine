# Check if MOSKA_ROOT_PATH environment variables exists.
# If it does not, we run the top-level __init__.py file, which will create it.
import os
import sys
def __initialize_pkg__():
    # Add the parent folder to the path
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root)
    # Define the path to the root folder of this library
    os.environ["MOSKA_ROOT_PATH"] = root
    #print("MOSKA_ROOT_PATH:", root)

if "MOSKA_ROOT_PATH" in os.environ:
    #print("MOSKA_ROOT_PATH environment variable found. Skipping top-level __init__.py file.")
    #print("MOSKA_ROOT_PATH:", os.environ["MOSKA_ROOT_PATH"])
    pass
else:
    #print("MOSKA_ROOT_PATH environment variable not found. Running top-level __init__.py file.")
    __initialize_pkg__()
