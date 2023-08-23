# This file is a very minimal example, and is provided for a friend
import sys
from MoskaEngine.Play.play_in_browser import play_as_human

if __name__ == '__main__':
    play_as_human(model_path="Model-nn1-BB", pred_format="bitmap",test=False)