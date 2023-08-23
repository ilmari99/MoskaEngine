import logging
import os
from MoskaEngine.Play.create_dataset import create_dataset
from MoskaEngine.Player.NewRandomPlayer import NewRandomPlayer
from MoskaEngine.Player.MoskaBot3 import MoskaBot3
from MoskaEngine.Player.NNEvaluatorBot import NNEvaluatorBot
from MoskaEngine.Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
from MoskaEngine.Play.PlayerWrapper import PlayerWrapper

if __name__ == '__main__':
    gamekwargs = {
        "log_level" : logging.DEBUG,
        "timeout" : 20,
        "gather_data":True,
        
        #"model_paths" : ["Model-nn1-BB"]
    }
    shared_pl_kwargs = {
        "log_level" : logging.DEBUG,
    }
    players = [PlayerWrapper(NewRandomPlayer, {"name" : "player1"}, infer_log_file=True),
               PlayerWrapper(MoskaBot3, {"name" : "player2"}, infer_log_file=True),
               PlayerWrapper(NNEvaluatorBot, {"name" : "player3", "model_id" : 0, "pred_format" : "bitmap"}, infer_log_file=True),
               PlayerWrapper(NNHIFEvaluatorBot, {"name" : "player4", "model_id" : 0, "pred_format" : "bitmap"}, infer_log_file=True),]
    
    nsuc = create_dataset(2, 5, "test_dataset", cpus=8, chunksize=1, use_HIF=False, verbose=True, players=players, gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 10, f"Expected 10 succesful games, got {nsuc}."
    print()
    nsuc = create_dataset(4, 2, "test_dataset",cpus = 2, chunksize=1, use_HIF=True, verbose=True, players="random", gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 8, f"Expected 8 succesful games, got {nsuc}."