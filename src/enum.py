from enum import Enum, auto


class State(Enum):
    """Enumeration of parser states used when decoding function-call JSON."""

    FIND_BRACKET = auto()
    WAIT_KEY = auto()
    READ_KEY = auto()
    WAIT_COLON = auto()
    WAIT_VALUE = auto()
    READ_VALUE = auto()
    WAIT_FINAL_OR_COMMA = auto()
    INVALID = auto()
    FINAL = auto()
