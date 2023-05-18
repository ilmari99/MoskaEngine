import os
import sys
def __initialize_pkg__():
    # Define the path to the root folder of this library
    MOSKA_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    #sys.path.append(MOSKA_ROOT_PATH)
    os.environ["MOSKA_ROOT_PATH"] = MOSKA_ROOT_PATH

if "MOSKA_ROOT_PATH" not in os.environ:
    __initialize_pkg__()

# Import subpackages so files importing this package can use them
from .Player import *
from .Game import *
from .Play import *




