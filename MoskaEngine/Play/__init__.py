import os
import sys
def __initialize_pkg__():
    # Add the parent parent folder to the path
    MRP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #sys.path.append(MRP)
    # Define the path to the root folder of this library
    MOSKA_ROOT_PATH = MRP
    os.environ["MOSKA_ROOT_PATH"] = MOSKA_ROOT_PATH

if "MOSKA_ROOT_PATH" not in os.environ:
    __initialize_pkg__()

# Import packages from top level, so that modules in this package can use them
from ..Player import *
from ..Game import *
