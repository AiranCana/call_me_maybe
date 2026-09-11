from enum import Enum, auto


class State(Enum):
    FIND_BRACKET = auto()
    WAIT_KEY = auto()
    READ_KEY = auto()
    WAIT_COLON = auto()
    WAIT_VALUE = auto()
    READ_VALUE = auto()
    WAIT_FINAL_OR_COMMA = auto()


class Parser_llm:
    
    def __init__(self, objetive_keys: list[str]):
        self.objetive_keys = objetive_keys
        self state = State.FIND_BRACKET
        self.buffer = ""
