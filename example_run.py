import os
import sys
from MoskaEngine.Play.play_in_browser import parse_args, run_as_command_line_program

if __name__ == '__main__':
    args = parse_args()
    print(args)
    run_as_command_line_program(" ".join(sys.argv[1:]))