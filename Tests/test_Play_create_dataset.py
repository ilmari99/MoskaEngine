import logging
import os

from MoskaEngine.Play.create_dataset import create_dataset

if __name__ == '__main__':
    gamekwargs = {
        "log_level" : logging.DEBUG,
        "timeout" : 12,
        "gather_data":True,
    }
    shared_pl_kwargs = {
        "log_level" : logging.DEBUG,
    }
    
    nsuc = create_dataset(2, 1, "test_dataset", 1, chunksize=1, use_HIF=False, verbose=True, players="random", gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 2, f"Expected 2 succesful games, got {nsuc}."
    print()
    nsuc = create_dataset(1, 2, "test_dataset", 1, chunksize=1, use_HIF=True, verbose=True, players="random", gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 2, f"Expected 2 succesful games, got {nsuc}."