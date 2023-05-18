from __future__ import annotations
from typing import Any, Callable, Iterable, List, TYPE_CHECKING, Sequence
if TYPE_CHECKING:
    from .Deck import Card

CARD_VALUES = tuple(range(2,15))                            # Initialize the standard deck
CARD_SUITS = ("C","D","H","S") 
CARD_SUIT_SYMBOLS = {"S":'♠', "D":'♦',"H": '♥',"C": '♣',"X":"X"}    #Conversion table
MAIN_DECK = None                                            # The main deck

def check_signature(sig : Sequence, inp : Sequence) -> bool:
    """ Check whether the input sequences types match the expected sequence.
    """
    for s, i in zip(sig,inp):
        if not issubclass(type(i),s):
            print("Expected type",s,"got",type(i))
            return False
    return True

def add_before(char : str, orig : str, add : str) -> str:
    """Add string before the first 'char' character of another string and return the new string.
    Args:
        string (str): log files prefix
        add (str): log files prefix
    Returns:
        str: new string
    """
    splitted = orig.split(char,maxsplit=1)
    if len(splitted) == 1:
        return splitted[0]
    return splitted[0] + str(add) + char + splitted[-1]

def suit_to_symbol(suits : Iterable or str) -> List or str:
    """Convert a suit to a symbol according to CARD_SUIT_SYMBOLS
    If suits is str, returns a string
    if suits is an iterable, returns a list

    Args:
        suits (Iterable or str): The suits to convert to symbols

    Returns:
        List or str
    """
    if isinstance(suits,str):
        return CARD_SUIT_SYMBOLS[suits]
    return [CARD_SUIT_SYMBOLS[s] for s in suits]

def check_can_fall_card(played_card : Card, fall_card : Card,trump : str) -> bool:
    """Returns true, if the played_card, can fall the fall_card.
    The played card can fall fall_card, if:
    - The played card has the same suit and is greater than fall_card
    - If the played_card is trump suit, and the fall_card is not.

    Args:
        played_card (Card): The card played from hand
        fall_card (Card): The card on the table
        trump (str): The trump suit of the current game

    Returns:
        bool: True if played_card can fall fall_card, false otherwise
    """
    success = False
    # Jos kortit ovat samaa maata ja pelattu kortti on suurempi
    if played_card.suit == fall_card.suit and played_card.value > fall_card.value:
        success = True
    # Jos pelattu kortti on valttia, ja kaadettava kortti ei ole valttia
    elif played_card.suit == trump and fall_card.suit != trump:
            success = True
    return success


class TurnCycle:
    """An implementation of a list-like structure, that loops over the list, if an index > len() is given.
    Doesn't yet support indexing with square brackets, but through the get_at_index -method.
    Also implements a pointer, that is increased when getting next elements in the list.
    This can be thought of as an indexer for a cycle structure; Players in Moska sometimes have turns based on their position in the table/cycle
    
    Eq.
    l = ['a', 'b','c','d']
    tc = TurnCycle(l)
    print(tc.get_at_index(3))
    >> d
    print(tc.get_at_index(5))
    >> b
    """
    population = []
    ptr = 0
    def __init__(self,population : List[Any],ptr : int = 0):
        """Initialize the TurnCycle instance.

        Args:
            population (List): Initialize the list structure
            ptr (int, optional): The starting index. Defaults to 0.
        """
        self.population = population
        self.ptr = ptr
        
    def get_at_index(self,index = None) -> Any:
        """Return the element at index, with the modulo operator.
        Returns the element at index % len(self)

        Args:
            index (int, optional): The index where you want the element. If the index is < len() then acts as a normal list, otherwise
            returns value at [index % len()] . Defaults to the current pointer.

        Returns:
            Any: the element at index
        """
        if index is None:
            index = self.ptr
        return self.population[index % len(self.population)]
        
    def get_next(self, incr_ptr : bool = True) -> Any:
        """Get the next element (self.ptr + 1) in the cycle. Increments pointer by default.

        Args:
            incr_ptr (bool, optional): Whether to increment pointer by 1. Defaults to True.

        Returns:
            Any: the next element (self.ptr + 1) in the cycle
        """
        out = self.get_at_index(self.ptr + 1)
        if incr_ptr:
            self.ptr += 1
        return out
    
    def get_prev(self, incr_ptr : bool = True) -> Any:
        """Get the previous element in the cycle.

        Args:
            incr_ptr (bool, optional): Whether to decrement the pointer by 1. Defaults to True.

        Returns:
            Any: The previous element
        """
        out = self.get_at_index(self.ptr - 1)
        if incr_ptr:
            self.ptr -= 1
        return out
    
    def get_prev_condition(self, cond : Callable, incr_ptr : bool =False) -> Any:
        """Returns the previous element in the cycle, that matches the condition.
        IF no match is found, returns an empty list. TODO: Maybe should raise Error?

        Args:
            cond (Callable): The callable to check whether elements in the population match the condition
            incr_ptr (bool, optional): Whether to move the pointer to the position of the latest previous match. Defaults to False.

        Returns:
            Any: The previous element that matches the condition
        """
        count = 1
        og_count = int(self.ptr)
        nxt = self.get_at_index()
        while not cond(nxt):
            nxt = self.get_prev()
            if count == len(self.population):
                nxt = []
                break
            count += 1
        if not incr_ptr:
            self.set_pointer(og_count)
        return nxt
    
    def add_to_population(self,val : Any, ptr : int = None) -> None:
        """Add a value to the population.

        Args:
            val (Any): Value to add to the population
            ptr (int, optional): Where to move the pointer. Defaults to no moving.
        """
        self.population.append(val)
        self.ptr += 0
        if ptr:
            self.ptr = ptr
    
    def get_next_condition(self,cond : Callable = lambda x : True, incr_ptr : bool = True) -> Any:
        """Returns the next element in the cycle, that matches the condition.
        IF no match is found, returns an empty list.

        Args:
            cond (Callable, optional): The condition to find a match. Defaults to lambda x : True.
            incr_ptr (bool, optional): Whether to increment the pointer to the position where the next condition was found. Unlike when getting a previous element, defaults to True.

        Returns:
            Any: The next element in the cycle that matches condition
        """
        count = 1
        og_count = int(self.ptr)
        nxt = self.get_next()
        while not cond(nxt):
            nxt = self.get_next()
            if count == len(self.population):
                nxt = []
                break
            count += 1
        if not incr_ptr:
            self.set_pointer(og_count)
        return nxt
    
    def set_pointer(self,ptr : int):
        """ Set the pointer of the TurnCycle -instance"""
        self.ptr = ptr
        
        
if __name__ == "__main__":
    tc = TurnCycle([0,1,2,3,4,5])
    print(tc.get_at_index())
    print(tc.get_next_condition(lambda x : x ==4))
    print(tc.ptr)
    print(tc.get_prev_condition(lambda x : x == 1))
    print(tc.ptr)
