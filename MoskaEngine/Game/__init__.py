import os
import sys
def __initialize_pkg__():
    # Add the parent parent folder to the path
    # Define the path to the root folder of this library
    MRP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MOSKA_ROOT_PATH = MRP
    os.environ["MOSKA_ROOT_PATH"] = MOSKA_ROOT_PATH

if "MOSKA_ROOT_PATH" not in os.environ:
    __initialize_pkg__()
