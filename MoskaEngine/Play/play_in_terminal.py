#!/usr/bin/env python3
import logging
import os
import time
from ..Game.Game import MoskaGame
from ..Player.HumanPlayer import HumanPlayer
from typing import Any, Callable, Dict, Iterable, List, Tuple
from ..Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
from .Utils import args_to_gamekwargs, make_log_dir, replace_setting_values
from .PlayerWrapper import PlayerWrapper

def get_human_players(model_path : str = "Model-nn1-bb",
                      pred_format : str = "bitmap",
                      ) -> List[PlayerWrapper]:
    """Returns a list of
    - Three identical PlayerWrapper(NNHIFEvaluatorBot)s, using the model found in model_path, with pred_format.
    - One PlayerWrapper(HumanPlayer) that can be controlled by the user.
    Args:
        model_path (str): Path to the model file.
        pred_format (str): The format of the predictions. Can be "bitmap" or "vector".
    Returns:
        List[PlayerWrapper]: A list of PlayerWrappers.
    """
    shared_kwargs = {"log_level" : logging.DEBUG,
                     "delay":1,
                     "requires_graphic":True}
    opp_shared_kwargs = {"max_num_states":8000,"max_num_samples":1000,"model_id" : model_path, "pred_format" : pred_format}
    players : List[PlayerWrapper] = []
    players.append(PlayerWrapper(HumanPlayer, {**shared_kwargs, **{"name":"Human","log_file":"human-{x}.log"}}))
    players.append(PlayerWrapper.from_config("NN2-HIF",1,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",2,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",3,**{**opp_shared_kwargs,**shared_kwargs}))
    return players

def get_test_human_players(model_path : str = "Model-nn1-BB",
                           pred_format : str = "bitmap",
                           ) -> List[PlayerWrapper]:
    """Returns a list of four identical PlayerWrapper(NNHIFEvaluatorBot)s, using the model found in model_path, with pred_format.
    This is used for testing purposes.
    """
    shared_kwargs = {"log_level" : logging.INFO,
                     "delay":0,
                     "requires_graphic":True,
                     "max_num_states":8000,
                     "max_num_samples":1000,
                     "model_id":model_path,
                     "pred_format":pred_format,
                     }
    opp_shared_kwargs = {"max_num_states":8000,"max_num_samples":1000,"model_id" : model_path, "pred_format" : pred_format}
    players = []
    players.append(PlayerWrapper.from_config("NN2-HIF",1,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",2,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",3,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",4,**{**opp_shared_kwargs,**shared_kwargs}))
    return players

def get_next_game_id(path : str, filename : str) -> int:
    """Returns the next available game id, by checking which files exist in the given path.
    """
    if "{x}" not in filename:
        raise ValueError("Filename must contain '{x}'")
    # if the folder does not exist, return 0
    if not os.path.exists(path):
        return 0
    # Pick any file that exists
    unique_filename = os.listdir(path)[0]
    i = -1
    while os.path.exists(os.path.join(path, unique_filename)):
        i += 1
        unique_filename = replace_setting_values({"filename" : filename},game_id = i)["filename"]
    print("Next game id",i)
    return i


def play_as_human(model_path = "Model-nn1-BB",
                  pred_format="bitmap",
                  test=False):
    """ Play as a human against three NNHIFEvaluatorBots. The order of the players is shuffled.
    """
    # Get a list of players
    if test:
        players = get_test_human_players(model_path = model_path, pred_format=pred_format)
    else:
        players = get_human_players(model_path = model_path, pred_format=pred_format)
    print(f"Using model path {model_path}")
    #players = get_test_human_players(model_path = "./Models/Model-nn1-fuller/model.tflite", pred_format="bitmap")
    cwd = os.getcwd()
    folder = "Human-Games"
    # Find the next available game id
    game_id = get_next_game_id("./" + folder,"HumanGame-{x}.log")
    gamekwargs = {
        "log_file" : "HumanGame-{x}.log",
        "players" : players,
        "log_level" : logging.DEBUG,
        "timeout" : 2000,
        "model_paths":model_path,
        "player_evals" : "plot",
        "print_format" : "basic",
        "in_console" : True,
        "in_web" : False
    }
    # Convert general game arguments to game specific arguments (replace '{x}' with game_id)
    game_args = args_to_gamekwargs(gamekwargs,players,gameid = game_id,shuffle = True)
    # Changes to the log directory for the duration of the game
    make_log_dir(folder,append=True)
    game = MoskaGame(**game_args)
    out = game.start()
    os.chdir(cwd)
    return out

def play_standard_game():
    out = play_as_human(model_path="Model-nn1-BB", pred_format="bitmap",test=False)
    return out

if __name__ == "__main__":
    start_time = time.time()
    play_as_human(model_path=os.environ["MOSKA_ROOT_PATH"] + "/Models/Model-nn1-BB/model.tflite", pred_format="bitmap",test=False)
    print("Time taken:",time.time() - start_time)
