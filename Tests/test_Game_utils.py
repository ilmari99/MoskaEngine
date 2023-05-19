import unittest
from typing import Sequence, List, Iterable
import sys
import os
from MoskaEngine.Game.utils import check_signature, add_before, suit_to_symbol, check_can_fall_card
from MoskaEngine.Game.utils import get_config_file, raise_config_not_found_error, get_model_file, raise_model_not_found_error
from MoskaEngine.Game.Deck import Card

class TestFunctions(unittest.TestCase):
    def test_check_signature(self):
        self.assertTrue(check_signature([int, str], [10, "hello"]))
        self.assertFalse(check_signature([int, str], ["world", 10]))
        self.assertTrue(check_signature([str], ["hello"]))
        self.assertFalse(check_signature([int], ["hello"]))
        self.assertTrue(check_signature([], []))
        
    def test_add_before(self):
        self.assertEqual(add_before(".", "file.txt", "new"), "filenew.txt")
        self.assertEqual(add_before(".", "file.txt", "_new"), "file_new.txt")
        self.assertEqual(add_before(".", "file.txt", ""), "file.txt")
        # If there is no "." in the string, the string is returned unchanged
        self.assertEqual(add_before(".", "file", "new"), "file")
        
    def test_suit_to_symbol(self):
        self.assertEqual(suit_to_symbol("H"), "♥")
        self.assertEqual(suit_to_symbol("D"), "♦")
        self.assertEqual(suit_to_symbol("C"), "♣")
        self.assertEqual(suit_to_symbol("S"), "♠")
        self.assertEqual(suit_to_symbol(["H", "D"]), ["♥", "♦"])
        self.assertEqual(suit_to_symbol(["C", "S"]), ["♣", "♠"])
        self.assertEqual(suit_to_symbol([]), [])
        
    def test_check_can_fall_card(self):
        played_card = Card(7, "H")
        fall_card = Card(5, "H")
        trump = "S"
        self.assertTrue(check_can_fall_card(played_card, fall_card, trump))
        
        played_card = Card(10, "D")
        fall_card = Card(2, "H")
        trump = "S"
        self.assertFalse(check_can_fall_card(played_card, fall_card, trump))
        
        played_card = Card(8, "S")
        fall_card = Card(3, "C")
        trump = "S"
        self.assertTrue(check_can_fall_card(played_card, fall_card, trump))
        
        played_card = Card(6, "C")
        fall_card = Card(6, "H")
        trump = "D"
        self.assertFalse(check_can_fall_card(played_card, fall_card, trump))

    def test_read_all_existing_configs(self):
        # Load the already existing config files from root + "/Play/PlayerConfigs/*.json"
        existing_configs = os.listdir(os.environ["MOSKA_ROOT_PATH"] + "/Play/PlayerConfigs/")
        existing_configs = [config for config in existing_configs if config.endswith(".json")]
        existing_config_names = [os.path.splitext(config)[0] for config in existing_configs]

        for existing_config, config_name in zip(existing_configs, existing_config_names):
            # Test the function
            result = get_config_file(config_name)
            # Assert the result:
            if not result:
                self.fail(f"Config file {config_name} not found.")
            elif result != os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + "/Play/PlayerConfigs/" + existing_config):
                self.fail(f"Config file {config_name} returned path {result},but expected {os.path.abspath(os.environ['MOSKA_ROOT_PATH'] + '/Play/PlayerConfigs/' + existing_config)}")

    def test_read_predefined_config_names(self):
        predef_names = ["NN1-MIF", "NN1-HIF", "NN2-MIF", "NN2-HIF", "Bot3"]
        for predef_name in predef_names:
            # Test the function
            result = get_config_file(predef_name)
            # Assert the result:
            if not result:
                self.fail(f"Config file {predef_name} not found.")
            elif result != os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + "/Play/PlayerConfigs/" + predef_name + ".json"):
                self.fail(f"Config file {predef_name} returned path {result},but expected {os.path.abspath(os.environ['MOSKA_ROOT_PATH'] + '/Play/PlayerConfigs/' + predef_name + '.json')}")

    def test_get_config_file_nonexistent_file(self):
        # Test the function with a non-existent file
        config = "nonexistent_config"
        result = get_config_file(config)
        # Assert the result
        self.assertEqual(result, "")

    def test_raise_config_not_found_error(self):
        # Test the function
        config = "test_config"
        with self.assertRaises(FileNotFoundError) as context:
            raise_config_not_found_error(config)
        
        one_of = os.listdir(os.environ["MOSKA_ROOT_PATH"] + "/Play/PlayerConfigs/")
        one_of = [os.path.splitext(config)[0] for config in one_of]
        # Assert the exception message
        expected_message = f"Config file {config} not found. Use a custom file, or one of: {one_of}"
        self.assertEqual(str(context.exception), expected_message)

    def test_read_all_existing_models(self):
        # Load the already existing model files from root + "/Play/Models/*.tflite"
        existing_models = os.listdir(os.environ["MOSKA_ROOT_PATH"] + "/Models/")
        existing_model_abs_paths = [os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + "/Models/" + model + "/model.tflite") for model in existing_models]
        for existing_model, model_abs_path in zip(existing_models, existing_model_abs_paths):
            # Test the function
            result = get_model_file(existing_model)
            # Assert the result:
            if not result:
                self.fail(f"Model file {existing_model} not found.")
            elif result != model_abs_path:
                self.fail(f"Model file {existing_model} returned path {result},but expected {model_abs_path}")

    def test_read_predefined_model_names(self):
        predef_names = ["NN1V0", "NN1", "NN2"]
        for predef_name in predef_names:
            # Test the function
            result = get_model_file(predef_name)
            # Assert the result:
            if not result:
                self.fail(f"Model file {predef_name} not found.")
            elif result != os.path.abspath(os.environ["MOSKA_ROOT_PATH"] + "/Models/" + predef_name + ".tflite"):
                self.fail(f"Model file {predef_name} returned path {result},but expected {os.path.abspath(os.environ['MOSKA_ROOT_PATH'] + '/Models/' + predef_name + '.tflite')}")


    def test_get_model_file_nonexistent_file(self):
        # Test the function with a non-existent file
        model = "nonexistent_model"
        result = get_model_file(model)

        # Assert the result
        self.assertEqual(result, "")

    def test_raise_model_not_found_error(self):
        # Test the function
        model = "test_model"
        with self.assertRaises(FileNotFoundError) as context:
            raise_model_not_found_error(model)
        one_of = os.listdir(os.environ["MOSKA_ROOT_PATH"] + "/Models/")
        # Assert the exception message
        expected_message = f"Model file {model} not found. Use a custom .tflite model or one of: {one_of}"
        self.assertEqual(str(context.exception), expected_message)


if __name__ == '__main__':
    unittest.main()

        
if __name__ == "__main__":
    unittest.main()
