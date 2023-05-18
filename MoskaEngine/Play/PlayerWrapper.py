import os
import sys
from ..Player.AbstractPlayer import AbstractPlayer
from typing import Any, Callable, Dict, Iterable, List, Tuple
from .Utils import replace_setting_values, CLASS_MAP
import json
"""
This file contains the PlayerWrapper class, which is used to wrap a player class and settings into a single object.
This object is then used to create a player instance. It is done this way to ease multiprocessing, and create filenames based on the game number.
"""

class PlayerWrapper:
    """ Wraps a player class and settings into a single object.
    Avoid ugly code, which uses a tuple of (player_class, settings : Callable) everywhere.
    """
    def __init__(self, player_class: AbstractPlayer, settings: Dict[str, Any], infer_log_file = False, number = -1):
        """ Settings should have '{x}' somewhere in it, which will be replaced by the game number.
        """
        if not issubclass(player_class,AbstractPlayer):
            raise ValueError(f"Player class {player_class} is not recognized as any subclass of {AbstractPlayer}")
        if not isinstance(settings, dict):
            raise TypeError(f"Settings must be a dict, but is {settings}")
        if infer_log_file and not 'log_file' in settings:
            name = settings.get("name", player_class.__name__)
            settings["log_file"] = "Game_{x}-" + name + ".log"
        # If the user wants to create multiple instances of the same player,
        # add a number to the name and log file.
        if number >= 0:
            settings["name"] = settings["name"] + f"_{number}"
            if "log_file" in settings:
                settings["log_file"] = settings["log_file"].split(".")[0] + f"_{number}.log"
            else:
                Warning("No log file (or infer) specified, but number is specified.")
        self.player_class = player_class
        self.settings = settings.copy()
        return
    
    @classmethod
    def from_config(cls, config : str, number = -1, **kwarg_overwrite) -> None:
        """ Only works on relative paths, due to a weird issue in spawning processes.
        Initialize a player wrapper from a json file.
        Since this is used in parallel, from a different process, the config file must be specified as a string.
        Later calls in the same main process just return the same object as in the first call.
        """

        if not os.path.isfile(config):
            config = "." + config
        if not os.path.isfile(config):
            raise FileNotFoundError(f"Config file {config} not found.")
        with open(config, 'r') as f:
            config = json.load(f)
        player_class = config["player_class"]
        settings = config["settings"]
        # Convert to absolute path if needed
        # This is very hacky, but again the processes are spawned in a weird way in the multiprocessing module.
        if "model_id" in settings and not settings["model_id"].isnumeric():
            # First search from given path. If not found search MOSKA_ROOT_PATH
            given_path = settings["model_id"]
            if not os.path.isfile(settings["model_id"]):
                settings["model_id"] = os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + given_path.strip("."))
            if not os.path.isfile(settings["model_id"]):
                raise FileNotFoundError(f"Model file {given_path} OR {settings['model_id']} not found.")
            settings["model_id"] = os.path.abspath(settings["model_id"])
        settings.update(kwarg_overwrite)
        player_class = CLASS_MAP[player_class]
        return cls(player_class, settings, number = number)

    def _get_instance_settings(self, game_id : int) -> None:
        """ Create a new settings dict, with the game id replaced.
        """
        # Create a new dict, so that the original settings are not changed.
        instance_settings = replace_setting_values(self.settings, game_id)
        return instance_settings
    
    def __repr__(self) -> str:
        return f"PlayerWrapper({self.player_class.__name__}, {self.settings})"
    
    def __call__(self, game_id : int = 0,instance_settings = None) -> AbstractPlayer:
        """ Create a player instance.
        """
        if not instance_settings:
            instance_settings = self._get_instance_settings(game_id)
        return self.player_class(**instance_settings)