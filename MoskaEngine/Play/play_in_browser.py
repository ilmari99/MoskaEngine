#!/usr/bin/env python3
import argparse
import logging
import os
import random
import sys
import sys
from ..Game.Game import MoskaGame
from typing import Any, Callable, Dict, Iterable, List, Tuple
from ..Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
from ..Player.HumanJsonPlayer import HumanJsonPlayer
from ..Player.HumanTestPlayer import HumanTestPlayer
from .Utils import args_to_gamekwargs, make_log_dir,get_random_players, replace_setting_values
from .PlayerWrapper import PlayerWrapper
from argparse import ArgumentParser
import sys

def get_n_bot_players(n : int,
                      model_path : str = "Model-nn1-BB",
                      pred_format : str = "bitmap",
                      override_kwargs : Dict[str,Any] = {},
                      ) -> List[PlayerWrapper]:
    """Returns a list of n identical PlayerWrapper(NNHIFEvaluatorBot)s, using the model found in model_path, with pred_format.
    Args:
        n (int): The number of players to return.
        model_path (str): Path to the model file.
        pred_format (str): The format of the predictions. Can be "bitmap" or "vector".
    Returns:
        List[PlayerWrapper]: A list of PlayerWrappers.
    """
    shared_kwargs = {"log_level" : logging.DEBUG,
                     "delay":0.2,
                     "requires_graphic":True,
                        "max_num_states":8000,
                        "max_num_samples":1000,
                        "model_id" : model_path,
                        "pred_format" : pred_format,
                     }
    set_of_possible_names = ["Mikko", "Martti", "Kalle", "Riku", "Jussi", "Milla", "Laura", "Hansku", "Johanna", "Aaron", "Cecilia",
                             "Luuva", "Kukko","Sikala", "Cicceli", "Nanna", "Mooses","Aliica", "Pirkko", "Meeri", "Tuija"
                             ]
    letter_to_number_converter = {"a":4, "e":3, "i":1, "o":0, "T": 7, "S": 5}
    players : List[PlayerWrapper] = []
    current_base_names = []
    for i in range(n):
        # Select a random name from the list of possible names
        random_name = random.choice(set_of_possible_names)
        while random_name in current_base_names:
            random_name = random.choice(set_of_possible_names)
        current_base_names.append(random_name)
        # For one of the names, replace the vowels with numbers
        random_name_subs = "".join([str(letter_to_number_converter.get(letter,letter)) for letter in random_name.lower()])
        # Shuffle the names
        random_names = random.sample([random_name,random_name_subs],2)
        mandatory_kwargs = {"name":random_names[0], "log_file":f"{random_names[0]}.log"}
        players.append(PlayerWrapper.from_config("NN2-HIF",-1,**{**shared_kwargs, **override_kwargs, **mandatory_kwargs}))
    return players

def get_test_players(human_names : List[str] = ["Human"],
        model_path : str = "./model.tflite",
        pred_format : str = "bitmap",
        ) -> List[PlayerWrapper]:
    """Returns a list of four identical PlayerWrapper(NNHIFEvaluatorBot)s, using the model found in model_path, with pred_format.
    This is used for testing purposes.
    """
    shared_kwargs = {"log_level" : logging.INFO,
                     "delay":0.2,
                     "requires_graphic":True,
                     }
    human_players = []
    for name in human_names:
        human_players.append(PlayerWrapper(HumanTestPlayer, {**shared_kwargs, **{"name":name,"log_file":f"{name}.log"}}))
    bot_players = get_n_bot_players(4 - len(human_players),model_path=model_path,pred_format=pred_format)
    return human_players + bot_players

def get_multiple_human_players(human_names : List[str],
        model_path : str = "Model-nn1-BB",
        pred_format : str = "bitmap",
        ) -> List[PlayerWrapper]:
        """Returns a list of four players. First we create the human players, then we fill the rest with NNHIFEvaluatorBots.
        """
        human_kwargs = {"log_level" : logging.DEBUG,
                     "delay":0.2,
                     "requires_graphic":True,
                     }
        human_players = []
        for name in human_names:
            log_file = {"log_file":f"{name}.log"}
            human_players.append(PlayerWrapper(HumanJsonPlayer, {**{"name":name},**human_kwargs,**log_file},infer_log_file=False, force_log_file=True))
        print(f"Human players: {human_players}")
        # Fill the rest with NNHIFEvaluatorBots
        n_bots = 4 - len(human_players)
        bot_players = get_n_bot_players(n_bots,model_path=model_path,pred_format=pred_format,override_kwargs=human_kwargs)
        return human_players + bot_players

def multiplayer_game(
        human_names : List[str],
        model_path = "Model-nn1-BB",
        pred_format="bitmap",
        game_id = 0,
        folder="",
        test=False,
        ):
    """ Start a game with multiple human players. If we have less than 4 human players, the rest are NNHIFEvaluatorBots.
    """
    assert len(human_names) <= 4, "We can have at most 4 players"
    print(f"Starting game number {game_id} with players {human_names}")
    players = get_multiple_human_players(human_names,
                                         model_path = model_path,
                                         pred_format=pred_format
                                         )
    if test:
        players = get_test_players(human_names,
                                   model_path = model_path,
                                   pred_format=pred_format)

    cwd = os.getcwd()
    
    folder = folder if folder else os.path.join(cwd,"Games")
    
    gamekwargs = {
        "log_file" : "Game.log",
        "players" : players,
        "log_level" : logging.DEBUG,
        "timeout" : 2000,
        "model_paths":model_path,
        "player_evals" : "save-plot",
        "print_format" : "basic_with_card_symbols",
        # XOR of these should be true; either but not both
        "in_console" : False,
        "in_web" : True,
        "gather_jsons" : True,
    }
    # Convert general game arguments to game specific arguments (replace '{x}' with game_id)
    game_args = args_to_gamekwargs(gamekwargs,players,gameid = game_id,shuffle = True)
    # Changes to the log directory for the duration of the game
    make_log_dir(folder,append=True)
    game = MoskaGame(**game_args)
    out = game.start()
    # Check if there is a file Vectors/data*.csv
    vectors_content = os.listdir("Vectors")
    for file in vectors_content:
        if file.startswith("data") and file.endswith(".csv"):
            # Move it one up
            os.rename(os.path.join("Vectors",file),os.path.join(".","vectors.csv"))
            break
    if os.path.exists("Vectors"):
        # Remove Vectors
        os.rmdir("Vectors")
    
    os.chdir(cwd)
    
    return out

def parse_name_argument(name : str, sep=",") -> List[str]:
    """ Parse a string of names, separated by commas. If the string is empty, return an empty list.
    """
    if not name:
        return []
    return name.split(sep)


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
    parser.add_argument("--folder", type=str, default="", help="The folder where the games are saved.")
    args = parser.parse_args(inp[1:] if skip_first else inp)
    return args


# This can be imported and run as a function with a string of arguments
def run_as_command_line_program(args):
    args = parse_args(args,skip_first=True)
    print(args.name)
    names = parse_name_argument(args.name)
    print(names)
    out = multiplayer_game(human_names=names,test=args.test,game_id=args.gameid,folder=args.folder)
    #out = play_as_human(model_path = "Model-nn1-BB",
    #                    human_name=args.name, test=args.test, game_id=args.gameid)
    if out:
        sys.exit(0)
    else:
        sys.exit(1)
        
if __name__ == "__main__":
    run_as_command_line_program(sys.argv)
