import os
def __initialize_pkg__():
    # Define the path to the root folder of this library.
    # This is used to use data (models) inside this library
    MOSKA_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    os.environ["MOSKA_ROOT_PATH"] = MOSKA_ROOT_PATH

if "MOSKA_ROOT_PATH" not in os.environ:
    __initialize_pkg__()

# Import subpackages so files importing this package can use them
from .Player import *
from .Game import *
from .Play import *

__version__ = "0.1.5"




