#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import sys
from ..Game.Game import MoskaGame
from typing import Any, Callable, Dict, Iterable, List, Tuple
from ..Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
from ..Player.HumanJsonPlayer import HumanJsonPlayer
from .Utils import args_to_gamekwargs, make_log_dir,get_random_players, replace_setting_values
from .PlayerWrapper import PlayerWrapper
from argparse import ArgumentParser
import sys

def get_human_players(model_path : str = "Model-nn1-BB",
                      pred_format : str = "bitmap",
                      human_name = "Human",
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
                     "delay":0.02,
                     "requires_graphic":True
                     }
    opp_shared_kwargs = {"max_num_states":8000,"max_num_samples":1000,"model_id" : model_path, "pred_format" : pred_format}

    players : List[PlayerWrapper] = []
    players.append(PlayerWrapper(HumanJsonPlayer, {**shared_kwargs, **{"name":human_name,"log_file":"Game-{x}-" +f"{human_name}" + ".log"}}))
    players.append(PlayerWrapper.from_config("NN2-HIF",1,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",2,**{**opp_shared_kwargs,**shared_kwargs}))
    players.append(PlayerWrapper.from_config("NN2-HIF",3,**{**opp_shared_kwargs,**shared_kwargs}))
    return players

def get_test_players(model_path : str = "./model.tflite",
                           pred_format : str = "bitmap",
                           ) -> List[PlayerWrapper]:
    """Returns a list of four identical PlayerWrapper(NNHIFEvaluatorBot)s, using the model found in model_path, with pred_format.
    This is used for testing purposes.
    """
    shared_kwargs = {"log_level" : logging.INFO,
                     "delay":0.02,
                     "requires_graphic":True,
                     "max_num_states":8000,
                     "max_num_samples":1000,
                     "model_id":model_path,
                     "pred_format":pred_format,
                     }
    players = []
    players.append(PlayerWrapper.from_config("NN2-HIF",1,**shared_kwargs))
    players.append(PlayerWrapper.from_config("NN2-HIF",2,**shared_kwargs))
    players.append(PlayerWrapper.from_config("NN2-HIF",3,**shared_kwargs))
    players.append(PlayerWrapper.from_config("NN2-HIF",4,**shared_kwargs))
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
                  test=False,
                  human_name="Human",
                  game_id = 0
                  ):
    """ Play as a human against three NNHIFEvaluatorBots. The order of the players is shuffled.
    """
    print(f"Starting game number {game_id} of player {human_name}")
    # Get a list of players
    if test:
        players = get_test_players(model_path = model_path, pred_format=pred_format)
    else:
        players = get_human_players(model_path = model_path, pred_format=pred_format, human_name=human_name)
    #players = get_test_human_players(model_path = "./Models/Model-nn1-fuller/model.tflite", pred_format="bitmap")
    cwd = os.getcwd()
    folder = human_name + "-Games"
    # Find the next available game id
    #game_id = get_next_game_id("./" + folder,"HumanGame-{x}.log")
    gamekwargs = {
        "log_file" : "HumanGame-{x}.log",
        "players" : players,
        "log_level" : logging.DEBUG,
        "timeout" : 2000,
        "model_paths":model_path,
        "player_evals" : "save",
        "print_format" : "basic_with_card_symbols",
        # XOR of these should be true; either but not both
        "in_console" : False,
        "in_web" : True,
    }
    # Convert general game arguments to game specific arguments (replace '{x}' with game_id)
    game_args = args_to_gamekwargs(gamekwargs,players,gameid = game_id,shuffle = True)
    # Changes to the log directory for the duration of the game
    make_log_dir(folder,append=True)
    game = MoskaGame(**game_args)
    out = game.start()
    os.chdir(cwd)
    return out

def parse_args(inp : List[str],skip_first = True):
    """ Parse a string of arguments, typically from the command line:
    inp = ["<program>", "--name", "Human", "--gameid", "0", "--test"]
    ignores the program name, and returns a namespace with the following attributes:
    - name : The name of the human player. Used in file naming and location.
    - gameid : The id of the game. Used in file naming and location.
    - test : Whether to actually use a human player or not
    """
    parser = argparse.ArgumentParser(description="Play as a human against three NNHIFEvaluatorBots")
    parser.add_argument("--name", type=str, default="Human", help="The name of the human player. Used in file naming and location.")
    parser.add_argument("--gameid", type=int, default=0, help="The id of the game. Used in file naming and location.")
    parser.add_argument("--test", action="store_true", help="Whether to actually use a human player or not")
    args = parser.parse_args(inp[1:] if skip_first else inp)
    return args


# This can be imported and run as a function with a string of arguments
def run_as_command_line_program(args):
    args = parse_args(args,skip_first=True)
    out = play_as_human(model_path = "Model-nn1-BB",
                        human_name=args.name, test=args.test, game_id=args.gameid)
    if out:
        sys.exit(0)
    else:
        sys.exit(1)

# This can be run as a command line program
if __name__ == "__main__":
    args = parse_args(sys.argv)
    out = play_as_human(model_path = "Model-nn1-BB",
                        human_name=args.name, test=args.test, game_id=args.gameid)
    if out:
        sys.exit(0)
    else:
        sys.exit(1)
