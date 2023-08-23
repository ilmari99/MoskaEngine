import os
import time
from MoskaEngine.Game.Game import MoskaGame
from MoskaEngine.Player.NewRandomPlayer import NewRandomPlayer
from MoskaEngine.Player.MoskaBot3 import MoskaBot3
from MoskaEngine.Player.NNEvaluatorBot import NNEvaluatorBot
from MoskaEngine.Player.NNHIFEvaluatorBot import NNHIFEvaluatorBot
import unittest
import shutil

"""
This file contains unit tests for the MoskaGame class.
The MoskaGame class is responsible for running a game between multiple players and logging the results.
The tests in this file cover the functionality of the MoskaGame class with different configurations of players and logging options.
"""

class TestMoskaGame(unittest.TestCase):
    def test_game_scratch_no_logging(self):
        """
        Test the MoskaGame class by running a game with 2 players who do not log anything.
        This test checks that no new files were created during the game.
        """
        curr_files = os.listdir()
        # Run a game with 2 players, who do not log anything
        game = MoskaGame(players=[MoskaBot3(name = "mb1"), MoskaBot3(name = "mb2")],
                         log_level=0,
                         timeout=10,
                         gather_data=False
                         )
        result = game.start()
        print(result)
        # Check the game EXIT_FLAG
        self.assertEqual(game.EXIT_FLAG, False)
        # Check that no new files were created
        self.assertEqual(curr_files, os.listdir())

    def test_game_scratch_with_logging(self):
        
        game = MoskaGame(players=[MoskaBot3(name = "mb1", log_file="mb1_test_game_scratch_with_logging.log"),
                                  MoskaBot3(name = "mb2", log_file="mb2_test_game_scratch_with_logging.log")],
                         log_file="test_game_scratch_with_logging.log",
                         in_folder="test_game_scratch_with_logging",
                         timeout=10,
                         gather_data=True
                         )
        result = game.start()
        print(result)
        # Check the game EXIT_FLAG
        self.assertEqual(game.EXIT_FLAG, False)
        # Check that new files exist in the folder
        files = os.listdir("test_game_scratch_with_logging")
        for file in files:
            if os.path.isdir(os.path.join(os.getcwd(),"test_game_scratch_with_logging",file)):
                self.assertEqual(file,"Vectors")
            else:
                self.assertIn(file, ["mb1_test_game_scratch_with_logging.log",
                                    "mb2_test_game_scratch_with_logging.log",
                                    "test_game_scratch_with_logging.log"])
        # Remove the folder
        shutil.rmtree("test_game_scratch_with_logging")

    
    def test_game_scratch_with_logging_NN(self):
        # Shared arguments for the NNEvaluatorBot
        sh_kwargs = {"model_id": 0,             # Specify the model by its index in the games list of models
                     "pred_format" : "bitmap",  # Specify the format of input to the model
                     "max_num_states" : 10,
                     "max_num_samples" : 10
                     }
        game_kwargs = {
            "model_paths": ["Model-nn1-BB"],    # Specify the model name. The model with this name is ready from the built-in models (included in library)
            "timeout": 10,
            "log_file": "test_game_scratch_with_logging_NN.log",
            "gather_data": True,
            "in_folder": "test_game_scratch_with_logging_NN",
        }
        # Run a game with 4 NN agents, who log
        game = MoskaGame(players=[NNHIFEvaluatorBot(name = "NN1", log_file="NN1.log", **sh_kwargs),
                                NNHIFEvaluatorBot(name = "NN2", log_file="NN2.log", **sh_kwargs),
                                NNHIFEvaluatorBot(name = "NN3", log_file = "NN3.log", **sh_kwargs),
                                NNHIFEvaluatorBot(name = "NN4", log_file = "NN4.log", **sh_kwargs),
                                ],
                         **game_kwargs,
                         )
        result = game.start()
        print(result)
        # Check the game EXIT_FLAG
        self.assertEqual(game.EXIT_FLAG, False)
        # Check that new files exist in the folder
        files = os.listdir("test_game_scratch_with_logging_NN")
        for file in files:
            if os.path.isdir(os.path.join(os.getcwd(),"test_game_scratch_with_logging_NN",file)):
                self.assertEqual(file,"Vectors")
            else:
                self.assertIn(file, ["NN1.log",
                                    "NN2.log",
                                    "NN3.log",
                                    "NN4.log",
                                    "test_game_scratch_with_logging_NN.log"])
        # Remove the folder
        shutil.rmtree("test_game_scratch_with_logging_NN")
    

if __name__ == '__main__':
    unittest.main()
