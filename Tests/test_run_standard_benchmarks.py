import unittest
from typing import List, Any, Callable
import sys
import os
import logging

from MoskaEngine.Play.benchmark import clean_up, standard_benchmark
from MoskaEngine.Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot


#TODO: Add a conversion to use the most common models with just a short name, e.g. "NN2" for the second iteration of the neural network.
if __name__ == '__main__':
    pl_type = NNHIFEvaluatorBot

    pl_kwargs = {
        "name" : "player",
        "model_id" : "ModelNN1",
        "pred_format" : "bitmap",
        "log_level" : logging.DEBUG,
        "max_num_states" : 1000,
    }

    game_kwargs = {
        "log_level" : logging.DEBUG,
        "gather_data" : True,
        "timeout" : 10,
        "model_paths" : ["ModelNN1"],
    }

    shared_player_kwargs = {
        "log_level" : logging.DEBUG,
    }

    results = []
    clean_up()
    #NOTE: Only run this benchmark on a heavy-duty machine, as it will take a long time to complete.
    standard_benchmark(pl_type, pl_kwargs, game_kwargs, cpus=14, chunksize=1, custom_shared_pl_kwargs=shared_player_kwargs)