import logging
from ..Game.Game import MoskaGame
from .MoskaBot3 import MoskaBot3


class HumanTestPlayer(MoskaBot3):
    """ This is basically Bot3, but with a different class name.
    For thge frontend to consider a player as a human player, the class name must contain the word "Human".
    I.e. The json of this player has "is_bot":False, only because the class name contains "Human".
    
    """
    def __init__(self, moskaGame: MoskaGame = None, name: str = "",
                 delay=0,
                 requires_graphic: bool = False,
                 log_level=logging.INFO, 
                 log_file="",
                 parameters={},
                 ):
        if name == "":
            name = "HumanTestPlayer"
        super().__init__(moskaGame, name, delay, requires_graphic, log_level, log_file, parameters)