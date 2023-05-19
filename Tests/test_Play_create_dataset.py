import logging
import os

from MoskaEngine.Play.create_dataset import create_dataset

if __name__ == '__main__':
    gamekwargs = {
        "log_level" : logging.DEBUG,
        "timeout" : 20,
        "gather_data":True,
    }
    shared_pl_kwargs = {
        "log_level" : logging.DEBUG,
    }
    
    nsuc = create_dataset(2, 5, "test_dataset", cpus=5, chunksize=1, use_HIF=False, verbose=True, players="random", gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 10, f"Expected 10 succesful games, got {nsuc}."
    print()
    nsuc = create_dataset(4, 2, "test_dataset",cpus = 2, chunksize=1, use_HIF=True, verbose=True, players="random", gamekwargs=gamekwargs, shared_player_kwargs=shared_pl_kwargs)
    assert nsuc == 8, f"Expected 8 succesful games, got {nsuc}."