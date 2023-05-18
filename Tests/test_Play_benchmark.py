import unittest
from typing import List, Any, Callable
import sys
import os
import logging

from MoskaEngine.Play.benchmark import run_benchmark, clean_up, BENCH1, BENCH2, BENCH3, BENCH4
from MoskaEngine.Player.NewRandomPlayer import NewRandomPlayer

if __name__ == '__main__':
    pl_type = NewRandomPlayer
    pl_kwargs = {
        "name" : "player1",
    }
    game_kwargs = {
        "log_level" : logging.INFO,
        "gather_data" : False,
        "timeout" : 6,
    }
    shared_player_kwargs = {
        "log_level" : logging.INFO,
    }
    results = []
    clean_up()
    for benchmark in [BENCH1, BENCH2, BENCH3, BENCH4]:
        results.append(run_benchmark(pl_type, pl_kwargs, benchmark, game_kwargs, shared_player_kwargs, cpus=1, chunksize=1,ngames=1))
    print(results)
