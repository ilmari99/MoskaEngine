import os
import sys
from ..Player.AbstractPlayer import AbstractPlayer
from typing import Any, Callable, Dict, Iterable, List, Tuple
from .Utils import replace_setting_values, CLASS_MAP, get_config_file, get_model_file, raise_config_not_found_error, raise_model_not_found_error
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
        # If the model_id is given as a number (index of the model in Game.model_paths)
        if "model_id" in settings and isinstance(settings["model_id"], int):
            settings["model_id"] = settings["model_id"]
        # Check if the input is something other than "all", and if it is, convert it to a path
        elif "model_id" in settings and settings["model_id"] != "all":
            # First search from given path. If not found search MOSKA_ROOT_PATH
            settings["model_id"] = self._convert_model_path(settings["model_id"])
        elif "model_id" in settings and settings["model_id"] == "all":
            settings["model_id"] = "all"
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
        og_config = config
        config = get_config_file(config)
        if not config:
            raise_config_not_found_error(og_config)
        with open(config, 'r') as f:
            config = json.load(f)
        player_class = config["player_class"]
        settings = config["settings"]
        if "model_id" in settings and not settings["model_id"].isnumeric():
            # First search from given path. If not found search MOSKA_ROOT_PATH
            settings["model_id"] = cls._convert_model_path(settings["model_id"])
        settings.update(kwarg_overwrite)
        player_class = CLASS_MAP[player_class]
        return cls(player_class, settings, number = number)
    
    @classmethod
    def _convert_model_path(self,path):
        if isinstance(path, list):
            return [self._convert_model_path(p) for p in path]
        model_path = get_model_file(path)
        if not model_path:
            raise_model_not_found_error(path)
        return model_path

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