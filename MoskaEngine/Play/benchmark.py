#!/usr/bin/env python3
import logging
import math
import os
import shutil
from ..Player.NewRandomPlayer import NewRandomPlayer
from ..Player.MoskaBot3 import MoskaBot3
from ..Player.AbstractPlayer import AbstractPlayer
from typing import Any, Callable, Dict, Iterable, List, Tuple
from ..Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
from ..Player.HeuristicEvaluatorBot import HeuristicEvaluatorBot
from .Simulate import play_games, get_loss_percents
from .Utils import make_log_dir
from .PlayerWrapper import PlayerWrapper

class Benchmark:
    def __init__(self, main_players : Tuple[PlayerWrapper], folder : str, game_kwargs : Dict[str,Any] = {}, shared_kwargs : Dict[str,Any] = {}):
        self.main_players = main_players
        self.folder = folder
        if not game_kwargs:
            game_kwargs = {
                "log_file" : "Game-{x}.log",
                "log_level" : logging.DEBUG,
                "timeout" : 60,
                "gather_data":False,
                "model_paths":[],
            }
        self.game_kwargs = game_kwargs
        self.shared_kwargs = shared_kwargs

    def calc_CI(self, loss_p, ngames):
        """ Agresti-Coull"""
        d = 1.96 * math.sqrt(loss_p * (1-loss_p) / ngames)
        return (loss_p - d, loss_p + d)
    
    def run(self, player : PlayerWrapper, cpus : int = -1, chunksize : int = 1, ngames : int = 1000, custom_game_kwargs : Dict[str,Any] = {},custom_shared_pl_kwargs : Dict[str,Any] = {}):
        """ Benchmark a player against a set of predefined models.
        """
        custom_game_kwargs = custom_game_kwargs.copy()
        models = self.game_kwargs.copy().get("model_paths", [])
        if "model_paths" in custom_game_kwargs:
            models += custom_game_kwargs["model_paths"]
            custom_game_kwargs.pop("model_paths")
        models = [os.path.abspath(m) for m in models]
        models = list(set(models))

        # Game arguments
        gamekwargs = {**self.game_kwargs, **custom_game_kwargs}
        players = [player] + self.main_players
        for pl in players:
            pl.settings = {**self.shared_kwargs, **pl.settings, **custom_shared_pl_kwargs}
        # Make the log directory and change to it
        make_log_dir(self.folder)
        results = play_games(players, gamekwargs, ngames=ngames, cpus=cpus, chunksize=chunksize,shuffle_player_order=True,verbose=False)
        loss_perc = get_loss_percents(results)
        print(f"Confidence interval of {player.settings['name']}: {self.calc_CI(loss_perc.get(player.settings['name'], 0)/100, ngames)}")
        os.chdir("..")
        return loss_perc.get(player.settings["name"], 0)

BENCH1 = Benchmark(
    main_players=[
        PlayerWrapper.from_config("NN1-MIF", number = 1),
        PlayerWrapper(MoskaBot3,{"name" : "B3", "log_file":"Game-{x}-B3.log"}),
        PlayerWrapper(HeuristicEvaluatorBot, {"name" : f"HEV1","log_file":"Game-{x}-HEV1.log","max_num_states":1000}),
    ],
    folder="Benchmark1",
    game_kwargs={
        "log_file" : "Game-{x}.log",
        "log_level" : logging.WARNING,
        "timeout" : 60,
        "gather_data":False,
        "model_paths":["ModelMB11-260"],
    },
    shared_kwargs={
        "log_level" : logging.WARNING,
    }
)

BENCH2 = Benchmark(
    main_players=[
        PlayerWrapper.from_config("NN1-MIF", number = 1),
        PlayerWrapper.from_config("NN1-MIF", number = 2),
        PlayerWrapper.from_config("NN1-MIF", number = 3),
    ],
    folder="Benchmark2",
    game_kwargs={
        "log_file" : "Game-{x}.log",
        "log_level" : logging.WARNING,
        "timeout" : 60,
        "gather_data":False,
        "model_paths":["ModelMB11-260"],
    },
    shared_kwargs={
        "log_level" : logging.WARNING,
    }
)

BENCH3 = Benchmark(
    main_players=[
        PlayerWrapper.from_config("Bot3", number = 1),
        PlayerWrapper.from_config("Bot3", number = 2),
        PlayerWrapper.from_config("Bot3", number = 3),
    ],
    folder="Benchmark3",
    game_kwargs={
        "log_file" : "Game-{x}.log",
        "log_level" : logging.WARNING,
        "timeout" : 60,
        "gather_data":False,
        "model_paths":[],
    },
    shared_kwargs={
        "log_level" : logging.WARNING,
    }
)

BENCH4 = Benchmark(
    main_players=[
        PlayerWrapper(NewRandomPlayer,{"name" : "R1", "log_file":"Game-{x}-R1.log"}),
        PlayerWrapper(NewRandomPlayer,{"name" : "R2", "log_file":"Game-{x}-R2.log"}),
        PlayerWrapper(NewRandomPlayer,{"name" : "R3", "log_file":"Game-{x}-R3.log"}),
    ],
    folder="Benchmark4",
    game_kwargs={
        "log_file" : "Game-{x}.log",
        "log_level" : logging.WARNING,
        "timeout" : 60,
        "gather_data":False,
        "model_paths":[],
        "print_format" : "basic",
    },
    shared_kwargs={
        "log_level" : logging.WARNING,
    }
)

BENCH5 = Benchmark(
    main_players=[
        PlayerWrapper.from_config("NN2-HIF", number = 1),
        PlayerWrapper.from_config("NN2-HIF", number = 2),
        PlayerWrapper.from_config("NN2-HIF", number = 3),
    ],
    folder="Benchmark5",
    game_kwargs={
        "log_file" : "Game-{x}.log",
        "log_level" : logging.WARNING,
        "timeout" : 60,
        "gather_data":False,
        "model_paths":["Model-nn1-BB"],
    },
    shared_kwargs={
        "log_level" : logging.WARNING,
    }
)

def run_benchmark(player_type : AbstractPlayer,
                  pl_args : Dict,
                  benchmark : Benchmark,
                  game_kwargs : Dict,
                  custom_shared_pl_kwargs : Dict = {},
                  cpus : int = 10,
                  chunksize : int = 1,
                  ngames : int = 10,
                  ):
    game_kwargs = { **{
        "gather_data" : False,
        "log_level" : logging.WARNING
    },**game_kwargs
    }
    player = PlayerWrapper(player_type, pl_args)
    pl_loss = benchmark.run(player,cpus = cpus,chunksize=chunksize,ngames=ngames,custom_game_kwargs=game_kwargs,custom_shared_pl_kwargs=custom_shared_pl_kwargs)
    return pl_loss

def standard_benchmark(player_type, pl_args, game_kwargs, cpus=10,chunksize=3):
    game_kwargs = { **{
        "model_paths" : ["Model-nn1-BB"],
        "gather_data" : False,
        "log_level" : logging.WARNING
    },**game_kwargs
    }
    player_losses = {}
    for benchmark in [BENCH1,BENCH2,BENCH3,BENCH4]:
        result = run_benchmark(player_type, pl_args, benchmark, game_kwargs, cpus=cpus, chunksize=chunksize, ngames=2000)
        player_losses[benchmark.folder] = result

def clean_up():
    shutil.rmtree("./Benchmark1", ignore_errors=True)
    shutil.rmtree("./Benchmark2", ignore_errors=True)
    shutil.rmtree("./Benchmark3", ignore_errors=True)
    shutil.rmtree("./Benchmark4", ignore_errors=True)
    shutil.rmtree("./Benchmark5", ignore_errors=True)

if __name__ == "__main__":
    clean_up()
    pl_type = NewRandomPlayer
    pl_kwargs = {
        "name" : "player1",
    }
    game_kwargs = {
        "log_level" : logging.INFO,
        "gather_data" : False,
        "timeout" : 1,
    }
    shared_player_kwargs = {
        "log_level" : logging.INFO,
    }
    res = run_benchmark(pl_type, pl_kwargs, BENCH1, game_kwargs, shared_player_kwargs, cpus=1, chunksize=1,ngames=1)
    print(res)
    exit()
    # Specify the model paths
    game_kwargs = {
        "model_paths" : [os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + "/Models/Model-nn1-BB/model.tflite")],
        "gather_data" : False,
        "log_level" : logging.DEBUG
    }
    # Specify the player type
    player_type = NNHIFEvaluatorBot
    # Specify the player arguments, '{x}' will be replaced by the game number
    player_args = {"name" : "player",
                    "log_file":"Game-{x}-player.log",
                    "log_level":logging.DEBUG,
                    "max_num_states":1000,
                    "max_num_samples":100,
                    "pred_format":"bitmap",
                    "model_id":game_kwargs["model_paths"][0],
    }
    standard_benchmark(player_type, player_args, game_kwargs, cpus=40,chunksize=3)



