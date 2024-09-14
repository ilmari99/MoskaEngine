import contextlib
import functools
import json
import os
import time
import threading
import logging
import random
import numpy as np
from typing import Any, Callable, Dict, Generator, List, Tuple

from ..Player.AbstractPlayer import AbstractPlayer
from .GameState import FullGameState
from . import utils
from .Deck import Card, StandardDeck
from .CardMonitor import CardMonitor
#import tensorflow as tf is done at set_model_vars_from_path IF a path is given.
# This is to gain a speedup if not using tensorflow
from .Turns import PlayFallFromDeck, PlayFallFromHand, PlayToOther, InitialPlay, EndTurn, PlayToSelf, Skip, PlayToSelfFromDeck


class MoskaGame:
    """This is a class for a Moskagame. This class itself handles:
    - Creation of the game: deck, trump, etc.
    - Creation of the players, and starting their threads
    - Giving turns for the players
    - Handling of locking and unlocking of the game state
    - Making a move
    - The restoration of FullGameState when making a mock move
    - Logging
    - and in the end, file creation and writing

    This class most notably uses the CardMonitor and TurnCycle custom classes as components.
    They are used to monitor the cards on the table, and to rotate the turns of the players.

    During a game, the changes to this MoskaGame instance, is done by a subclass of Turn (Turns.py -file).
    The Turn -subclass is responsible for modifying this game instance (and its components),
    based on how the user calls the '_make_move' -method.

    """
    players : List[AbstractPlayer] = []     # List of players, with unique pids, and cards already in hand
    trump : str = ""                      # Trump suit, set when the moskaGame is started
    trump_card : Card = None              # Trump card
    cards_to_fall : List[Card] = []         # Current cards on the table, for the target to fall
    fell_cards : List[Card] = []            # Cards that have fell during the last turn
    turnCycle = utils.TurnCycle([],ptr = 0) # A TurnCycle instance, that rotates from the last to the first, created when players defined
    deck  : StandardDeck = None             # The deck belonging to the moskaGame. 
    threads : Dict[int,AbstractPlayer] = {} # A dictionary of threads with the threads native id as key, and the player as value
    log_file : str = ""                     # The file to which to write the logs, empty string means no logging
    log_level = logging.INFO                # The logging level
    name : str = __name__                   # The name of the game
    glog : logging.Logger = None            # The logger instance
    main_lock : threading.RLock = None      # The main lock of the game, used to lock the game state when a player is either calculating what move to make or making the move
    lock_holder = None                      # The player that currently holds the lock
    turns : dict = {}                       # A dictionary of turns, with the turn name as key, and the turn class as value
    timeout : float = 3                     # The timeout for the duration of the game. Started when start() is called, and ended when either an error occurs, or the game ends.
    random_seed = None                      # The random seed of the game. CURRENTLY NOT CONFIRMED TO WORK
    nplayers : int = 0                      # The number of players in the game
    card_monitor : CardMonitor = None       # The card monitor instance 
    __prev_lock_holder__ = None             # The previous lock holder, used to check if the lock holder has changed, to avoid one thread locking the game twice in a row
    GATHER_DATA : bool = True               # Whether to gather data or not
    EXIT_FLAG = False                       # Whether the game is running or not. If this is True, then no-one can obtain the lock, threads will stop, and start() will return
    IS_RUNNING = False                      # Currently no real use
    def __init__(self,
                 players : List[AbstractPlayer] = [],
                 log_file : str = "",
                 log_level = logging.INFO,
                 in_folder : str = ".",
                 timeout=3,
                 random_seed=None,
                 gather_data : bool = True,
                 model_paths : List[str] = [],
                 player_evals : str = "", # Either 'save', or 'plot' or ''
                 print_format : str = "basic", # Either 'basic', 'with_cards', 'with_evals', 'human'
                 deck : StandardDeck = None,
                 in_console : bool = False,
                 in_web : bool = False,
                 gather_jsons : bool = False,
                 ):
        """Initialize the game, by setting the deck, models, players, card monitor and some other variables.
        Args:
            deck (StandardDeck, optional): The deck to use. Defaults to None.
            players (List[AbstractPlayer], optional): The players to use. Defaults to []. If this is not empty, then nplayers is ignored.
            nplayers (int, optional): The number of players to use. Defaults to 0. DEPRECATED.
            log_file (str, optional): The file to which to write the logs. Defaults to os.devnull.
            log_level (logging, optional): The logging level. Defaults to logging.INFO.
            timeout (int, optional): The timeout for the game. Defaults to 3.
            random_seed ([type], optional): The random seed to use. Defaults to None.
            gather_data (bool, optional): Whether to gather data or not. Defaults to True. The gathered data will be written to a csv file.
            model_paths (List[str], optional): The paths to the models to use. Defaults to [""]. If the paths are empty, no neural network based models can be used.
        """
        self.nturns = 0
        self.in_folder = in_folder
        if in_console and in_web:
            raise ValueError("Cannot be in both console and web")
        self.in_console = in_console
        self.in_web = in_web
        self.has_graphics = in_console or in_web
        self.GATHER_DATA = gather_data
        self.IS_RUNNING = False
        # This plotting data is used if atleast one of the players requires graphic
        # The plot is about the progression of the state evaluations of each player (evals vs turns)
        self.player_evals = player_evals
        self.print_format = print_format
        self.gather_jsons = gather_jsons
        self.player_evals_data : Dict[int,List[int]] = {}
        self.threads = {}
        self.log_level = log_level
        os.makedirs(in_folder,exist_ok=True)
        self.log_file = os.path.join(in_folder,log_file) if log_file else os.devnull
        # Write the states of the game to a json file
        if self.gather_jsons:
            self.jsons_file = self.log_file
            if self.jsons_file != os.devnull:
                self.jsons_file = self.jsons_file.replace(".log",".json")
            with open(self.jsons_file,"w") as f:
                f.write("[\n")
        self.interpreters = []
        self.input_details = []
        self.output_details = []
        self.model_paths = model_paths
        self.set_model_vars_from_paths()
        self.random_seed = random_seed if random_seed else int(10000000*random.random())
        self.deck = deck if deck else StandardDeck(seed = self.random_seed)
        self.players = players
        self.timeout = timeout
        self.EXIT_FLAG = False
        self.card_monitor = CardMonitor(self)
        self._set_turns()
        self.glog.info(f"Game initialization complete.")


    def set_model_vars_from_paths(self) -> None:
        """Set the model paths, interpreters, input and output details from the model paths.
        This is used to load the models from the paths, and to set the input and output details of each model.

        The models must be tensorflow lite models.
        """
        if isinstance(self.model_paths,str):
            self.model_paths = [self.model_paths] if self.model_paths else []
        self.interpreters = []
        self.input_details = []
        self.output_details = []
        # Loop through the model paths, and convert shorthands to absolute paths and check that they all exist
        orig_paths = self.model_paths
        self.model_paths = [utils.get_model_file(path) for path in self.model_paths]
        if not self.model_paths:
            self.glog.info(f"No models specified.")
            return
        for i, path in enumerate(self.model_paths):
            if not path:
                utils.raise_model_not_found_error(orig_paths[i])
        self.glog.debug("Importing Tensorflow and loading models from paths: {}".format(self.model_paths))
        # We import tensorflow only if there are models to load! This speeds up the process.
        # This also allows the user to run the game without tensorflow installed.
        # Furthermore, Tensorflow cannot be run with optimizations (-OO flag),
        # So this allows us to simulate games without tensorflow bots with optmizations
        # All output can not be disabled from tflite, without a custom build, so we just minimize it
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        import tensorflow as tf
        for path in self.model_paths:
            try:
                interpreter = tf.lite.Interpreter(model_path=path)
            except Exception as e:
                self.glog.error(f"Could not load model from path {path}.")
                raise e
            interpreter.allocate_tensors()
            self.interpreters.append(interpreter)
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            self.output_details.append(output_details)
            self.input_details.append(input_details)
        self.glog.info(f"Loaded {self.model_paths} models.")
        self.glog.debug(f"Input details: {self.input_details}")
        self.glog.debug(f"Output details: {self.output_details}")
        return
    
    def model_predict(self, X : np.ndarray, model_id : (str or int) = "all") -> np.ndarray:
        """ Make a prediction with the model with the given id. The ID can either be an integer or a string (path to the model or 'all').
        The input shape must be (n, input_size), where n is the number of samples, and input_size is the input size of the model,
        even if the model is a convolutional model.
        If the model has a signature, with a channel dimension, then the input shape is resized for that model.

        Args:
            X (np.ndarray): The input data to the model. The shape must be (n, input_size)
            model_id (str or int, optional): The id of the model to use. Defaults to "all". If "all", then all models are used.
        """
        # See which models the player wants to use
        if model_id == "all":
            model_id = list(range(len(self.interpreters)))
        if isinstance(model_id,int):
            model_id = [model_id]
        if isinstance(model_id,str):
            try:
                model_id = [self.model_paths.index(model_id)]
            except:
                raise Exception(f"Could not find model path {model_id} in {self.model_paths}")
        player_logger = self.threads[threading.get_native_id()].plog
        output_data = []
        if not isinstance(X,np.ndarray):
            try:
                player_logger.debug(f"Converting X {type(X)} to np.ndarray")
                X = np.array(X)
            except:
                raise Exception(f"Could not convert {X} to np.ndarray")
        if not model_id:
            raise Exception(f"model_id is empty: {model_id}")
        if not X.shape:
            raise Exception(f"X.shape is empty: {X.shape}")
        if not self.interpreters:
            raise Exception("No model found for prediction. Model paths: {}".format(self.model_paths))
        for m_id,model_info in enumerate(zip(self.interpreters,self.input_details,self.output_details)):
            interpreter,input_details,output_details = model_info
            if m_id not in model_id:
                continue
            if len(X.shape) != len(input_details[0]["shape"]):
                prev_shape = X.shape
                X = np.expand_dims(X, axis=-1)
            interpreter.resize_tensor_input(input_details[0]["index"],X.shape)
            interpreter.allocate_tensors()
            interpreter.set_tensor(input_details[0]['index'], X)
            interpreter.invoke()
            out = interpreter.get_tensor(output_details[0]['index'])
            output_data.append(out)
        output_data = np.array(output_data)
        return output_data
    
    def _set_turns(self):
        """Set the turns dictionary, which contains the callable turn classes."""
        self.turns = {
        "PlayFallFromHand" : PlayFallFromHand(self),
        "PlayFallFromDeck" : PlayFallFromDeck(self),
        "PlayToOther" : PlayToOther(self),
        "PlayToSelf" : PlayToSelf(self),
        "InitialPlay" : InitialPlay(self),
        "EndTurn": EndTurn(self),
        "Skip":Skip(self),
        "PlayToSelfFromDeck":PlayToSelfFromDeck(self)
        }
        return


    def __getattribute____(self, __name: str) -> Any:
        """ This is a fail safe to prevent dangerous access to MoskaGame
        attributes from outside the main or player threads, when the game is locked.
        Only some attributes are seen as non-accessable.
        This is called always when somewhere is for example called a = game.deck.
        """
        non_accessable_attributes = ["card_monitor", "deck", "turnCycle", "cards_to_fall", "fell_cards", "players"]
        if __name in non_accessable_attributes and self.threads and threading.get_native_id() != self.lock_holder:
            raise threading.ThreadError(f"Getting MoskaGame attribute with out lock!")
        return object.__getattribute__(self,__name)
    
    def __setattr__(self, name, value):
        """ This is called everytime an attribute of this instance is set with the syntax 'game.attribute = value'.
        Prevents access to MoskaGame attributes from outside the main or player threads, when the game is locked.
        Also used for ensuring that inter-related attributes are set correctly, such as the players and the turnCycle.
        """
        if name == "EXIT_FLAG":
            super.__setattr__(self, name, value)
            return
        if name != "lock_holder" and self.threads and threading.get_native_id() != self.lock_holder:
            raise threading.ThreadError(f"Setting MoskaGame attribute with out lock!")
        super.__setattr__(self, name, value)
        # If setting the players, set the turnCycle and the new deck
        if name == "players":
            self._set_players(value)
            self.glog.debug(f"Set players to: {value}")
        # If setting the log_file, set the logger
        if name == "log_file" and value:
            assert isinstance(value, str), f"'{name}' of MoskaGame attribute must be a string"
            self.name = value.split(".")[0]
            self._set_glogger(value)
        # If setting nplayers, create random players and set self.players
        if name == "nplayers":
            self.players = self.players if self.players else self._get_random_players(value)
            self.glog.debug(f"Created {value} random players.")
        # If setting the random seed, set the random seed
        if name == "random_seed":
            random.seed(value)
            self.glog.info(f"Set random_seed to {self.random_seed}")
        if self.threads and self.lock_holder and (self is not self.threads[self.lock_holder]) and name not in ["deck", "fell_cards", "cards_to_fall"]:
            self.glog.debug(f"Setting MoskaGame attribute {name} to {value}")
        return
    
    def _set_players(self,players : List[AbstractPlayer]) -> None:
        """Here self.players is already set to players
        Here we set the deck, turncycle, and each players moskagame attribute.
        """
        assert isinstance(players, list), f"'players' of MoskaGame attribute must be a list"
        self.deck = StandardDeck(seed=self.random_seed)
        for pl in players:
            pl.moskaGame = self
        self.turnCycle = utils.TurnCycle(players)
        return
    
    def _set_glogger(self,log_file : str) -> None:
        """Set the games logger `glog`.
        Get a logger with the name of the game, and set the log level to self.log_level.
        Format the log messages to be: "name:levelname:message"
        Set the log file to be the log_file (likely self.log_file) argument.
        """
        self.glog = logging.getLogger(self.name)
        self.glog.setLevel(self.log_level)
        fh = logging.FileHandler(log_file,mode="w",encoding="utf-8")
        formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
        fh.setFormatter(formatter)
        self.glog.addHandler(fh)
        self.glog.debug(f"Set GameLogger (glog) to file {log_file}")
        return
    
    def _create_locks(self) -> None:
        """ Initialize the RLock (re-enterable lock) for the game. """
        self.main_lock = threading.RLock()
        self.glog.debug("Created RLock")
        return
    
    @contextlib.contextmanager
    def get_lock(self,player=None) -> bool:
        """A wrapper around getting the moskagames main_lock.
        Sets the lock_holder to the obtaining threads id
        and yields True if the lock was obtained.
        If the lock was not obtained, yields False.
        If the lock was obtained, but the game is exiting, yields False.
        If the lock was obtained, but the lock_holder is not in self.threads, yields False.
        If the lock was obtained, but the lock_holder is the same as the previous lock_holder, yields False.
        Returns none
        """
        with self.main_lock as lock:
            self.lock_holder = threading.get_native_id()
            if self.lock_holder == self.__prev_lock_holder__:
                self.lock_holder = None
                yield False
                return
            if self.lock_holder not in self.threads:
                self.lock_holder = None
                print(f"Game {self.log_file}: Couldn't find lock holder id {self.lock_holder}!")
                yield False
                return
            # Yields false if the game is exiting
            if self.EXIT_FLAG:
                self.lock_holder = None
                yield False
                return
            if not player:
                player = self.threads[self.lock_holder]
            if isinstance(player, AbstractPlayer):
                self.glog.debug(f"{player.name} has locked the game.")
            # Here we tell the player that they have the key
            yield True
            if len(set(self.cards_to_fall)) != len(self.cards_to_fall):
                print(f"Game log {self.log_file} failed, DUPLICATE CARD")
                self.glog.error(f"Game log {self.log_file} failed, DUPLICATE CARD")
                self.EXIT_FLAG = True
                raise AssertionError(f"DUPLICATE CARD in game {self.log_file}")
            self.__prev_lock_holder__ = self.lock_holder
            self.lock_holder = None
        if isinstance(player, AbstractPlayer):
            self.glog.debug(f"{player.name} has unlocked the game.")
            # Sleep a random time between 0 and 100 ms
            sleep_time = random.random()/10
            time.sleep(sleep_time)
        return
    
    def _reduce_logging_wrapper(self,func) -> Callable:
        """ A wrapper, that reduces the logging of a player in the wrapped function.
        This is used in the _make_move function, if mock is True.
        """
        functools.wraps(func)
        def wrapper(*args,**kwargs):
            self.glog.setLevel(logging.WARNING)
            player = self.threads[self.lock_holder]
            player.plog.setLevel(logging.WARNING)
            out = func(*args,**kwargs)
            player.plog.setLevel(player.log_level)
            self.glog.setLevel(self.log_level)
            return out
        return wrapper
    
    def _move_call_wrapper(self,move_call) -> Callable:
        """ A wrapper that wraps a move call, and catches AssertionErrors. """
        functools.wraps(move_call)
        def wrapper(*args,**kwargs):
            move = args[0]
            try:
                move_call(*args[1:])
            except AssertionError as ae:
                
                return False, str(ae)
            except TypeError as te:
                return False, str(te)
            self.card_monitor.update_from_move(move,args[1:])
            return True, ""
        return wrapper
    
    def _make_move(self,move,args,mock=False) -> Tuple[bool,str]:
        """ This is called from an AbstractPlayer -instance.
        This is the heart of a game simulation.

        This function takes a move and the arguments for that move, and does a few checks to make sure the move is valid.
        It then calls the corresponding function from Turns.py, which changes the attributes of this game, or raises an assertion error.
        If an assertion error is raised, this function returns False and the error message.
        Else, this function returns True and an empty string.

        Each running player thread waits for the lock, and after acquiring it, figures out what to play.
        After figuring what to play, it calls this method with the move and the arguments to the move.

        This is called in a context manager, so the lock is already acquired.
        This calls the move from Turns.py, which raises an AssertionError if the move is not playable.

        TODO: Change AssertioErrors to custom errors.
        """
        # If the lock holder isn't correct, raise an error
        if self.lock_holder != threading.get_native_id():
            raise threading.ThreadError(f"Making moves is supposed to be implicit and called in a context manager after acquiring the games lock")
        # If incorrect move, raise an error
        if move not in self.turns.keys():
            raise NameError(f"Attempted to make move '{move}' which is not recognized as a move in Turns.py")
        # Find the function for the move
        move_call = self.turns[move]
        # Find the calling player
        player = self.threads[self.lock_holder]
        # If the move isn't a mock move, increment the turn counter
        if not mock:
            self.nturns += 1
            # If we have either console or web graphics, print the move
            if self.has_graphics:
                def _print_fmt(x):
                    if isinstance(x,AbstractPlayer):
                        return x.name
                    elif isinstance(x,Callable):
                        return ""
                    if self.in_web and x and isinstance(x,(list,tuple,dict)) and len(x) > 0:
                        if isinstance(x,dict):
                            return {k.as_str(symbol=False):v.as_str(symbol=False) for k,v in x.items()}
                        return [c.as_str(symbol=False) for c in x]
                    else:
                        return x
                self.glog.info(f"Turn number: {self.nturns}: '{player.name}' called '{move}' with args {[_print_fmt(a) for a in args]}")
                print(f"Turn number: {self.nturns}: '{player.name}' played '{move}' with arguments {[_print_fmt(a) for a in args]}")
        # Create a function for making the move, so we can wrap it with the _reduce_logging_wrapper if mock is True
        move_call = self._move_call_wrapper(move_call)
        if mock:
            move_call = self._reduce_logging_wrapper(move_call)
        suc, msg = move_call(move,*args)
        if not suc:
            player.plog.warning(msg)
            return False, msg
        if not mock and self.player_evals:
            state = FullGameState.from_game(self,copy=False)
            for pl in self.players:
                model_id, fmt = self._get_players_model_or_copy(pl)
                pl_eval = self.model_predict(np.array(state.as_perspective_vector(pl,fmt=fmt),dtype = np.float32),model_id = model_id)
                pl_eval = round(float(pl_eval),2)
                if pl.pid not in self.player_evals_data.keys():
                    self.player_evals_data[pl.pid] = []
                self.player_evals_data[pl.pid].append(pl_eval)
        if not mock:
            #if self.log_level == logging.DEBUG:
            #    self.glog.info(f"{self._basic_repr_with_all_evals_and_cards()}")
            #elif self.log_level == logging.INFO:
            #    self.glog.info(f"{self._basic_repr_with_cards()}")
            player._set_rank()
            if self.in_console and move != "Skip":
                print(f"{self._basic_repr_with_human_evals()}")
            elif self.in_web and move != "Skip":
                # Print the full json in one line
                s = self._basic_json_repr()
                s = s.replace("\n","")
                s = s.replace(" ","")
                s = s.replace("\t","")
                print(s)
            if self.gather_jsons and move != "Skip":
                with open(self.jsons_file,"a") as f:
                    s = self._basic_json_repr()
                    f.write(s)
                    f.write(",\n")
        # If the move is something else than Skip, have all players play again, except the player who just played
        # The target player can only end their turn, after every opponent has played a Skip move. Kind of like checking in poker.
        if move != "Skip":
            for pid, pl in enumerate(self.players):
                if pl.thread_id == self.lock_holder or pl.rank is not None:
                    continue
                pl.ready = False
        return True, ""
    
    def _make_mock_move(self,move,args,state_fmt="FullGameState") -> FullGameState:
        """ Makes a move, like '_make_move', but returns the game state after the move and restores self and attributes to its original state.
        This is basically a wrapper around _make_move, which saves the game state before the move, and restores it after the move.
        """
        state = FullGameState.from_game(self,copy=True)
        #self.glog.debug("Saved state data. Setting logger to level WARNING for Mock move")
        player = args[0]

        # Normally play the move; change games state precisely as it would actually change, but with different logging
        success, msg = self._make_move(move,args,mock=True)
        if not success:
            raise AssertionError(f"Mock move failed: {msg}")
        if state_fmt == "FullGameState" or "FullGameState-Depr":
            new_state = FullGameState.from_game(self,copy=True)
        else:
            raise NameError(f"Argument 'state_fmt' was not recognized. Given argument: {state_fmt}")
        # Save the new game state, for evaluation of the move
        state.restore_game_state(self,check=False)
        is_eq, msg = state.is_game_equal(self,return_msg=True)
        if not is_eq:
            raise AssertionError(f"Mock move failed: {msg}")
        # Return the new_state
        return new_state
    
    def get_turn_player_name(self) -> AbstractPlayer:
        """ Return player who is the lock holder.
        """
        try:
            return self.threads[self.lock_holder].name
        except KeyError:
            self.glog.warning(f"Could not find player with thread id {self.lock_holder}")
            return None
        except AttributeError:
            self.glog.warning(f"Lock holder is not a player")
    
    def _basic_json_repr(self) -> str:
        """ Return a json representation of the game state.
        """
        json_dict = {
            "trump_card" : self.trump_card.as_str(symbol=False),
            "deck_left" : len(self.deck.cards),
            "cards_to_kill" : [c.as_str(symbol=False) for c in self.cards_to_fall],
            "killed_cards" : [c.as_str(symbol=False) for c in self.fell_cards],
            "target" : self.get_target_player().name,
            "initiator" : self.get_initiating_player().name,
            "turn" : self.get_turn_player_name(),
            # Load players dictionaires from jsons
            "players" : [json.loads(pl.as_json()) for pl in self.players]
        }
        return json.dumps(json_dict,indent=4)
    
    def _basic_repr(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the number of cards they have in their hand.
        """
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pl in self.players:
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            s += f" : {len(self.card_monitor.player_cards[pl.name])}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def _basic_repr_with_cards(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the cards (counted) they have in their hand.
        """
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pl in self.players:
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            s += f" : {self.card_monitor.player_cards[pl.name]}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def _get_players_model_or_copy(self, pl):
        # If player doesn't have model_id or pred_format, use default values. Atleast one player needs to have these.
        if not hasattr(pl,"model_id") or not hasattr(pl,"pred_format"):
            pl_to_copy = self.get_players_condition(lambda x : x.name != pl.name and hasattr(x,"model_id") and hasattr(x,"pred_format"))[0]
            if not pl_to_copy:
                self.EXIT_FLAG = True
                raise AttributeError(f"Can not play with these settings (requires_graphic) if no player has a model.")
            model_id = pl_to_copy.model_id
            pred_format = pl_to_copy.pred_format
        else:
            model_id = pl.model_id
            pred_format = pl.pred_format
        return model_id, pred_format
    
    def _basic_repr_with_all_evals(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the cards (counted) they have in their hand.
        """
        state = FullGameState.from_game(self, copy = False)
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pid,pl in enumerate(self.players):
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            pl_eval = self.player_evals_data.get(pl.pid,[0])[-1]
            s += f"({pl_eval})"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            s += f" : {len(self.card_monitor.player_cards[pl.name])}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def _basic_repr_with_all_evals_and_cards(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the cards (counted) they have in their hand.
        """
        state = FullGameState.from_game(self, copy = False)
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pid,pl in enumerate(self.players):
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            pl_eval = self.player_evals_data.get(pl.pid,[0])[-1]
            s += f"({pl_eval})"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            s += f" : {self.card_monitor.player_cards[pl.name]}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def _basic_repr_with_human_evals(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the cards (counted) they have in their hand.
        """
        state = FullGameState.from_game(self, copy = False)
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pid,pl in enumerate(self.players):
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            if "human" in type(pl).__name__.lower():
                pl_eval = self.player_evals_data.get(pl.pid,[0])[-1]
                s += f"({pl_eval})"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            s += f" : {len(self.card_monitor.player_cards[pl.name])}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def _basic_repr_with_card_symbols(self) -> str:
        """ Print the current state of the game,
        showing number of cards left in the deck, the trump card, target,
        and each players name and the cards (counted) they have in their hand.
        """
        s = f"Trump card: {self.trump_card}\n"
        s += f"Deck left: {len(self.deck.cards)}\n"
        for pl in self.players:
            s += f"{pl.name}{' (TG)' if pl is self.get_target_player() else ''}"
            s += " " * max(16 - len(s.split("\n")[-1]),1)
            ncards = len(self.card_monitor.player_cards[pl.name])
            s += f" : {[Card(-1, 'X') for _ in range(ncards)]}\n"
        s += f"Cards to kill : {self.cards_to_fall}\n"
        s += f"killed cards : {self.fell_cards}\n"
        return s
    
    def __repr__(self) -> str:
        """ What to print when calling print(self).
        If REDUCED_PRINT is True, only print that information, which is visible to a player in a real game.
        Else, also print information about each players cards (perfect memory), and the players personal evaluations.
        """
        if self.print_format == "basic":
            return self._basic_repr()
        if self.print_format == "basic_with_card_symbols":
            return self._basic_repr_with_card_symbols()
        elif self.print_format == "basic_with_cards":
            return self._basic_repr_with_cards()
        elif self.print_format == "basic_with_all_evals":
            return self._basic_repr_with_all_evals()
        elif self.print_format == "basic_with_all_evals_and_cards":
            return self._basic_repr_with_all_evals_and_cards()
        elif self.print_format == "human":
            return self._basic_repr_with_human_evals()
        elif self.print_format == "json":
            return self._basic_json_repr()
        else:
            raise NameError(f"Argument 'print_format' was not recognized. Given argument: {self.print_format}")
    
    def _start_player_threads(self) -> None:
        """ Starts all player threads.

        Clears the 'cards_to_fall' and 'fell_cards' lists.
        Adds self to the 'threads' dictionary.
        Starts all player threads. with the lock.      
        """
        self.cards_to_fall.clear()
        self.fell_cards.clear()
        # Add self to allowed threads
        self.threads[threading.get_native_id()] = self
        self.glog.info("Starting player threads")
        with self.get_lock() as ml:
            for pl in self.players:
                tid = pl._start()
                self.threads[tid] = pl
            self.glog.info("Started player threads")
            assert len(set([pl.pid for pl in self.players])) == len(self.players), f"A non-unique player id ('pid' attribute) found."
            self.card_monitor.start()
            self.glog.info("Started card monitor.")
            self.IS_RUNNING = True
        return
    
    def _join_threads(self) -> None:
        """ Join all threads.
        This does not actually call the join method, but rather constantly checks if any thread has reported to have failed.
        If any thread has EXIT_STATUS 2, the game is terminated.
        The game timeouts if after 'timeout' seconds, any thread is still alive.
        """
        self.glog.info("Main thread waiting for player threads")
        start = time.time()
        while time.time() - start < self.timeout and any([pl.thread.is_alive() for pl in self.players]):
            time.sleep(0.1)
            # Check if any thread has failed
            if any((pl.EXIT_STATUS == 2 for pl in self.players)):
                failed_player = self.get_players_condition(lambda x : x.EXIT_STATUS == 2)[0]
                self.glog.error(f"Player {failed_player.name} failed. File: {failed_player.log_file}. Exiting.")
                with self.get_lock() as ml:
                    print(f"Game with log {self.log_file} failed.")
                    self.glog.error(f"Game FAILED. Exiting.")
                    self.EXIT_FLAG = True
                return False
        # Check if any thread has timed out
        if any((pl.EXIT_STATUS != 1 for pl in self.players)):
            print(f"Game with log {self.log_file} timedout.")
            self.glog.error(f"Game timedout after {self.timeout} seconds. Exiting.")
            self.EXIT_FLAG = True
            return False
        self.glog.info("Threads finished")
        return True
    
    
    def get_initiating_player(self) -> AbstractPlayer:
        """ Return the player, whose turn it is/was to initiate the turn aka. play to an empty table.
        """
        active = self.get_target_player()
        ptr = int(self.turnCycle.ptr)
        out = self.turnCycle.get_prev_condition(cond = lambda x : x.rank is None and x is not active,incr_ptr=False)
        # This can happen, if a player has just finished, then for a short while the player is both the target and the initiating player.
        if not out:
            out = self.turnCycle.get_prev_condition(cond = lambda x : x.rank is None,incr_ptr=False)
        if not out:
            raise RuntimeError("No initiating player found.")
        assert self.turnCycle.ptr == ptr, "Problem with turnCycle"
        return out
    
    def get_players_condition(self, cond : Callable = lambda x : True) -> List[AbstractPlayer]:
        """ Get a list of players that return True when condition is applied.
        """
        return list(filter(cond,self.players))
    
    def add_cards_to_fall(self,add : List[Card]) -> None:
        """Add a list of cards to fall.
        This is quite useless.
        """
        self.cards_to_fall += add
        return
        
    def get_target_player(self) -> AbstractPlayer:
        """Return the player, who is currently the target; To who cards are played to.
        """
        return self.turnCycle.get_at_index()
    
    def _set_trump(self) -> None:
        """Sets the trump card of the MoskaGame.
        Takes the top-most card, checks the suit, and checks if any player has the 2 of that suit in hand.
        If some player has, then it swaps the cards.
        Places the card at the bottom of the deck.
        """
        self.glog.info(f"Setting trump card")
        assert len(self.players) > 1 and len(self.players) <= 8, "Too few or too many players"
        trump_card = self.deck.pop_cards(1)[0]
        self.trump = trump_card.suit
        # Get the player with the trump 2 in hand
        p_with_2 = self.get_players_condition(cond = lambda x : any((x.suit == self.trump and x.rank==2 for x in x.hand.cards)))
        # Swap the card if possible
        self._orig_trump_card = trump_card
        if p_with_2:
            assert len(p_with_2) == 1, "Multiple people have valtti 2 in hand."
            p_with_2 = p_with_2[0]
            p_with_2.hand.add([trump_card])
            trump_card = p_with_2.hand.pop_cards(cond = lambda x : x.suit == self.trump and x.rank == 2)[0]
            self.glog.info(f"Removed {trump_card} from {p_with_2.name}")
            if self.in_console:
                print(f"Player {p_with_2.name} had trump 2 in hand. Swapping {self._orig_trump_card} with {trump_card}")
            if self.in_web:
                # Write without unicode
                print(f"Player {p_with_2.name} had trump 2 in hand. Swapping {self._orig_trump_card.as_str(symbol=False)} with {trump_card.as_str(symbol=False)}")
        self.trump_card = trump_card
        self.deck.place_to_bottom(self.trump_card)
        self.glog.info(f"Placed {self.trump_card} to bottom of deck.")
        return
    
    def get_player_state_vectors(self, shuffle = True, balance = True) -> List[List]:
        """ Get the state vectors of all players.
        If shuffle is True, the vectors are shuffled.
        If balance is True, the vectors are balanced, i.e. the number of vectors of players who lost and players who did not lose are equal.
        """
        losers = []
        not_losers = []
        # Combine the players vectors into one list
        for pl in self.players:
            # If the player lost, append 0 to the end of the vector, else append 1
            pl_not_lost = 0 if pl.rank == len(self.players) else 1
            for state in pl.state_vectors:
                if pl_not_lost == 0:
                    losers.append(state + [0])
                else:
                    not_losers.append(state + [1])
        if balance:
            state_results = losers + random.sample(not_losers,min(len(losers),len(not_losers)))
        else:
            state_results = losers + not_losers
        if shuffle:
            random.shuffle(state_results)
        return state_results
        
        
    def get_random_file_name(self,min_val = 1, max_val = 1000000000):
        fname = "data_"+str(random.randint(int(min_val),int(max_val)))+".csv"
        tries = 0
        while os.path.exists(fname) and tries < 1000:
            fname = "data_"+str(random.randint(0,max_val))+".csv"
            tries += 1
        if tries == 1000:
            print("Could not find a unique file name. Saving to custom file name.")
            fname = "data_new_"+str(random.randint(0,max_val))+".csv"
        return fname
    
    def plot_evaluations(self):
        try:
            import matplotlib.pyplot as plt
        except:
            print("Could not import matplotlib.pyplot. Skipping plotting.")
            return
        fig, ax = plt.subplots()
        for pl in self.players:
            ax.plot(self.player_evals_data[pl.pid],label=pl.name)
        ax.legend()
        ax.set_xlabel("Turns",fontsize=20)
        ax.set_ylabel("Evaluation",fontsize=20)
        ax.set_title("Evaluations of players",fontsize=20)
        fig.set_size_inches(15,10)
        ax.grid()
        if self.player_evals == "plot":
            plt.show()
        elif self.player_evals == "save-plot":
            save_to_file = self.log_file
            save_to_file = save_to_file.replace(".log",".png")
            plt.savefig(os.path.join(self.in_folder,save_to_file))
        return
    
    def start(self) -> List[Tuple[str,int]]:
        """ The main method of MoskaGame. Sets the trump card, locks the game to avoid race conditions between players,
        initializes and starts the player threads.
        After that, the players play the game, only one modifying the state of the game at a time.
        """
        if len(set([pl.name for pl in self.players])) != len(self.players):
            raise ValueError("Players must have unique names.")
        self._set_trump()
        self._create_locks()
        self.glog.info(f"Starting the game with seed {self.random_seed}...")
        os.makedirs(self.in_folder,exist_ok=True)
        old_dir = os.getcwd()
        os.chdir(self.in_folder)
        self._start_player_threads()
        self.glog.info(f"Started moska game with players {[pl.name for pl in self.players]}")
        # Wait for the threads to finish, fail, or timeout
        success = self._join_threads()
        if self.gather_jsons:
            with open(self.jsons_file,"a") as f:
                # Remove the last ',\n'
                f.truncate(f.tell()-3)
                # Write the end of the json
                f.write("\n]")
        os.chdir(old_dir)
        if not success:
            return None
        self.glog.info("Final ranking: ")
        # Each players name and rank
        ranks = [(p.name, p.rank) for p in self.players]
        state_results = []
        # If gathering data, save the data to a file
        if self.GATHER_DATA:
            balance, shuffle = (False, False) if self.has_graphics else (True, True)
            state_results = self.get_player_state_vectors(shuffle = shuffle, balance = balance)
            vector_path = os.path.join(self.in_folder,"Vectors")
            os.makedirs(vector_path,exist_ok=True)
            with open(os.path.join(vector_path,self.get_random_file_name()),"w") as f:
                data = str(state_results).replace("], [","\n").replace(" ","")
                data = data.strip("[]")
                f.write(data)
        if self.player_evals_data:
            for pid, pl in enumerate(self.players):
                self.glog.info(f"{pl.name} : {self.player_evals_data[pid]}")
        # Close the logger
        for handler in self.glog.handlers:
            handler.close()
        # If plotting data, plot the data
        if "plot" in self.player_evals:
            self.plot_evaluations()
        # Sort the ranks by rank
        ranks = sorted(ranks,key = lambda x : x[1] if x[1] is not None else float("inf"))
        for p,rank in ranks:
            self.glog.info(f"#{rank} - {p}")
        return ranks