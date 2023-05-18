import unittest
from typing import Sequence, List, Iterable
import sys
import os
from MoskaEngine.Game.utils import check_signature, add_before, suit_to_symbol, check_can_fall_card
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
        
if __name__ == "__main__":
    unittest.main()
