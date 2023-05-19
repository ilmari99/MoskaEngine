#!/usr/bin/env python3
import logging
import os
import sys
from typing import Any, Dict
import warnings
import time
import sys
from .Simulate import play_games, get_loss_percents
from .Utils import make_log_dir, get_random_players

def create_dataset(nrounds : int,
                   num_games : int,
                   folder : str,
                   cpus : int,
                   chunksize : int = 4,
                   use_HIF : bool = False,
                   verbose : bool=True,
                   nplayers : int = 4,
                   players = "random",
                   gamekwargs : Dict[str,Any] = {},
                   shared_player_kwargs : Dict[str,Any] = {}
                   ) -> int:
    """Creates a dataset by playing games between random players.
    """
    if os.path.exists(folder):
        warnings.warn(f"Folder {folder} already exists. Overwriting.")
    if nplayers != 4:
        raise NotImplementedError("Only 4 players supported at the moment.")
    CWD = os.getcwd()
    model_paths = ["Model-nn1-BB","ModelNN1"]
    gamekwargs = {
        **{"log_file" : "Game-{x}.log",
        "log_level" : logging.DEBUG,
        "timeout" : 30,
        "gather_data":True,
        "model_paths":model_paths,},
        **gamekwargs
    }
    print(f"Creating dataset with {nrounds} rounds and {num_games} games per round.")
    print(f"Total games: {nrounds*num_games}.")
    print(f"Using {cpus} cpus and chunksize {chunksize}.")
    print(f"Using HIF: {use_HIF}.")
    time_taken = 0
    nsuccesful = 0
    for i in range(nrounds):
        start_time = time.time()
        acting_players = get_random_players(nplayers, use_HIF=use_HIF,shared_kwargs=shared_player_kwargs) if players == "random" else players
        print(f"Round {i+1} players:")
        for p in acting_players:
            print(p)
        make_log_dir(folder,append=True)
        results = play_games(acting_players, gamekwargs, ngames=num_games, cpus=cpus, chunksize=chunksize,shuffle_player_order=True,verbose=verbose)
        print(results)
        nsuccesful += len(tuple(filter(lambda x: x is not None, results)))
        os.chdir(CWD)
        if not verbose:
            get_loss_percents(results)
        end_time = time.time()
        time_taken += (end_time - start_time)
        print(f"Round {i+1} took {end_time - start_time} seconds.")
        print(f"Estimated time remaining: {(time_taken/(i+1) * (nrounds - i-1))/60} minutes.")
    print(f"Finished. Total time taken: {time_taken/60} minutes.")
    return nsuccesful

if __name__ == "__main__":
    folder = "./Dataset"
    players = "random"
    create_dataset(nrounds=2,num_games=10,chunksize=3,folder=folder,cpus=5,use_HIF=False,players=players,verbose=False)
