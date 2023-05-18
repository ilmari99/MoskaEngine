import unittest
from collections import Counter
import sys
import os
from MoskaEngine.Game.Deck import Card, StandardDeck

class TestCard(unittest.TestCase):
    def test_card_attributes(self):
        card = Card(5, "S", kopled=True, score=10)
        self.assertEqual(card.value, 5)
        self.assertEqual(card.suit, "S")
        self.assertTrue(card.kopled)
        self.assertEqual(card.score, 10)
        # Check that raises TypeError if setting value or suit again
        with self.assertRaises(TypeError):
            card.value = 10
        with self.assertRaises(TypeError):
            card.suit = "H"
        card.kopled = False
        card.score = 5
        self.assertFalse(card.kopled)
        self.assertEqual(card.score, 5)
        
    def test_card_hash(self):
        card1 = Card(5, "S")
        card2 = Card(5, "S")
        card3 = Card(10, "H")
        self.assertEqual(hash(card1), hash(card2))
        self.assertNotEqual(hash(card1), hash(card3))
        
    def test_card_representation(self):
        card = Card(5, "S")
        self.assertEqual(repr(card), "5♠")
        card = Card(10, "H")
        self.assertEqual(repr(card), "10♥")
        
    def test_card_comparison(self):
        card1 = Card(5, "S")
        card2 = Card(10, "H")
        self.assertTrue(card1 < card2)
        self.assertFalse(card2 < card1)
        self.assertTrue(card1 == Card(5, "S"))
        self.assertFalse(card1 == card2)

class TestStandardDeck(unittest.TestCase):
    def test_deck_creation(self):
        deck = StandardDeck(shuffle=False)
        self.assertEqual(len(deck), 52)
        counts = Counter(card.value for card in deck.cards)
        self.assertEqual(counts, {2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4, 10: 4, 11: 4, 12: 4, 13: 4, 14: 4})
        
    def test_deck_shuffle(self):
        deck = StandardDeck(seed=42)
        original_order = list(deck.cards)
        deck.shuffle()
        shuffled_order = list(deck.cards)
        self.assertNotEqual(original_order, shuffled_order)
        
    def test_deck_pop_cards(self):
        deck = StandardDeck(shuffle=False)
        # Pop two twos and one three
        cards = deck.pop_cards(5)
        self.assertEqual(len(deck), 47)
        self.assertEqual(len(cards), 5)
        self.assertEqual(Counter(card.value for card in cards), {2: 4, 3:1})
        # pop three threes, 4 fours and 3 fives
        cards = deck.pop_cards(10)
        self.assertEqual(len(deck), 37)
        self.assertEqual(len(cards), 10)
        self.assertEqual(Counter(card.value for card in cards), {3 : 3, 4: 4, 5: 3})
        
if __name__ == "__main__":
    unittest.main()