import unittest
from typing import List, Any, Callable
import sys
import os
import logging

from MoskaEngine.Play.benchmark import run_benchmark, clean_up, BENCH1, BENCH2, BENCH3, BENCH4
from MoskaEngine.Player.NewRandomPlayer import NewRandomPlayer

if __name__ == '__main__':
    pl_type = NewRandomPlayer
    # Arguments for this player
    pl_kwargs = {
        "name" : "player1",
    }
    # Arguments for the game
    game_kwargs = {
        "log_level" : logging.DEBUG,
        "gather_data" : False,
        "timeout" : 20,
    }
    # Arguments shared by all players
    shared_player_kwargs = {
        "log_level" : logging.DEBUG,
    }
    results = []
    clean_up()
    for benchmark in [BENCH1, BENCH2, BENCH3, BENCH4]:
        results.append(run_benchmark(pl_type, pl_kwargs, benchmark, game_kwargs, shared_player_kwargs, cpus=5, chunksize=1,ngames=5))
    print(results)
