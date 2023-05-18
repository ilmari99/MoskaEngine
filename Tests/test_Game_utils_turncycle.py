import unittest
from typing import List, Any, Callable
import sys
import os
from MoskaEngine.Game.utils import TurnCycle

class TestTurnCycle(unittest.TestCase):
    def test_get_at_index(self):
        tc = TurnCycle([1, 2, 3, 4])
        self.assertEqual(tc.get_at_index(2), 3)
        self.assertEqual(tc.get_at_index(5), 2)
        
    def test_get_next(self):
        tc = TurnCycle([1, 2, 3, 4])
        self.assertEqual(tc.get_next(), 2)
        self.assertEqual(tc.get_next(), 3)
        self.assertEqual(tc.get_next(), 4)
        self.assertEqual(tc.get_next(), 1)
        
    def test_get_prev(self):
        tc = TurnCycle([1, 2, 3, 4])
        self.assertEqual(tc.get_prev(), 4)
        self.assertEqual(tc.get_prev(), 3)
        self.assertEqual(tc.get_prev(), 2)
        self.assertEqual(tc.get_prev(), 1)
        
    def test_get_prev_condition(self):
        def is_even(num):
            return num % 2 == 0
        
        tc = TurnCycle([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(tc.ptr,0)
        # TODO: Increment pointer by default.
        self.assertEqual(tc.get_prev_condition(is_even), 10)
        self.assertEqual(tc.get_prev_condition(is_even), 8)
        self.assertEqual(tc.get_prev_condition(is_even), 6)
        self.assertEqual(tc.get_prev_condition(is_even), 4)
        
    def test_add_to_population(self):
        tc = TurnCycle([1, 2, 3, 4])
        self.assertEqual(tc.population[0%len(tc.population)], 1)
        self.assertEqual(tc.population[1%len(tc.population)], 2)
        self.assertEqual(tc.population[2%len(tc.population)], 3)
        self.assertEqual(tc.population[3%len(tc.population)], 4)
        self.assertEqual(tc.population[4%len(tc.population)], 1)
        self.assertEqual(tc.population[5%len(tc.population)], 2)
        tc.add_to_population(5)
        self.assertEqual(tc.population[0%len(tc.population)], 1)
        self.assertEqual(tc.population[1%len(tc.population)], 2)
        self.assertEqual(tc.population[2%len(tc.population)], 3)
        self.assertEqual(tc.population[3%len(tc.population)], 4)
        self.assertEqual(tc.population[4%len(tc.population)], 5)
        self.assertEqual(tc.population[5%len(tc.population)], 1)
        # Check that the new element is added to the end of the list
        self.assertEqual(tc.get_at_index(4), 5)
        # Check that the pointer is not changed
        self.assertEqual(tc.ptr, 0)
        
        # Add element and set pointer to the new element
        # If we want to point to the new element, we need to add 1 to the index
        tc.add_to_population(6, len(tc.population)-1 + 1)
        self.assertEqual(tc.population[0%len(tc.population)], 1)
        self.assertEqual(tc.population[1%len(tc.population)], 2)
        self.assertEqual(tc.population[2%len(tc.population)], 3)
        self.assertEqual(tc.population[3%len(tc.population)], 4)
        self.assertEqual(tc.population[4%len(tc.population)], 5)
        self.assertEqual(tc.population[5%len(tc.population)], 6)
        self.assertEqual(len(tc.population), 6)
        self.assertEqual(tc.ptr, 5)
        self.assertEqual(tc.get_at_index(), 6)
        self.assertEqual(tc.get_at_index(), 6)
        self.assertEqual(tc.get_at_index(3), 4)
        self.assertEqual(tc.get_at_index(5), 6)
        self.assertEqual(tc.get_next(), 1)
        
    def test_get_next_condition(self):
        def is_odd(num):
            return num % 2 != 0
        
        tc = TurnCycle([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        # TODO: with get_next_condition, the current element is not checked
        # TODO: Add argument whether to check current element or not
        self.assertEqual(tc.get_next_condition(is_odd), 1)
        self.assertEqual(tc.get_next_condition(is_odd), 3)
        self.assertEqual(tc.get_next_condition(is_odd,incr_ptr=False), 3)
        self.assertEqual(tc.get_next_condition(is_odd, incr_ptr=False), 3)
        self.assertEqual(tc.get_next_condition(is_odd,check_curr = False), 5)
        
    def test_set_pointer(self):
        tc = TurnCycle([1, 2, 3, 4])
        tc.set_pointer(2)
        self.assertEqual(tc.get_at_index(), 3)
        tc.set_pointer(5)
        self.assertEqual(tc.get_at_index(), 2)
        
if __name__ == "__main__":
    unittest.main()
