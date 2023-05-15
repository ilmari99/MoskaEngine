import os
import sys
from Play.play_in_browser import parse_args, play_as_human

"""Example script to run a game in the browser."""

if __name__ == "__main__":
    args = parse_args()
    out = play_as_human(model_path = os.environ["MOSKA_ROOT_PATH"] + "/Models/Model-nn1-BB/model.tflite",
                        human_name=args.name, test=args.test, game_id=args.gameid)
    if out:
        sys.exit(0)
    else:
        sys.exit(1)