# MoskaEngine
A repository containing a card game and simulation engine for the card game "Moska". This repository was created as part of a BSc thesis at the University of LUT, Finland. The repository contains subpackages and modules to further study the card game of Moska and develop new AI agents. It allows efficient simulations, benchmarks, data gathering, and playing as a human.

The thesis can be read from: https://urn.fi/URN:NBN:fi-fe2023051644576

Development ideas and TODO: Ask me!

[This repository](https://github.com/LeeviKamarainen/Moska) by Leevi is under development, and will be a web application for playing Moska online! Currently, a web application is running at https://moska-online.com/, but it is a very crude version, which was only used to gather data from human players to the thesis.

Install by running:
`pip install MoskaEngine`

## Usage
To play a standard game (same as in https://moska-online.com/) in your terminal, you can create the following script:
```python
from MoskaEngine.Play.play_in_terminal import play_standard_game

# This doesn't take any arguments.
if __name__ == '__main__':
    play_game()
```

To use the game engine, for example, in a web application, you can use the following code:
```python
import sys
from MoskaEngine.Play.play_in_browser import run_as_command_line_program

# This command line program accepts the following arguments:
# --name <player_name> (default: "Human"), this is used to create a folder for the player.
# --gameid <game_id> (default: 0), this is used to determine the game id and to correctly store log files. The next game's id can be retrieved with MoskaEngine.Play.play_in_browser.get_next_game_id(<your-folder>)
# --test (default: False), if set to True, the game will be played with 4 AI agents, and no human.
if __name__ == '__main__':
    run_as_command_line_program(sys.argv)
```

Further customization is very much possible, but requires some knowledge of the MoskaEngine. Futher documentation might be added in the future.
