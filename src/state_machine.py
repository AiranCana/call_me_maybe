from enum import Enum, auto
from typing import Any


class State(Enum):
    FIND_BRACKET = auto()
    WAIT_KEY = auto()
    READ_KEY = auto()
    WAIT_COLON = auto()
    WAIT_VALUE = auto()
    READ_VALUE = auto()
    WAIT_FINAL_OR_COMMA = auto()
    FINAL = auto()


class Parser_llm:

    def __init__(self, objetive_keys: list[str]):
        self.objetive_keys = objetive_keys
        self.state = State.FIND_BRACKET.value
        self.buffer = ""
        self.actual_key = ""
        self.stract_data = {}
        self.tipe_value = ""
        self.read_dict_value = None

    def proces_token(self, token: str) -> None:
        for char in token:
            self.__trancriptor(char)

    def __trancriptor(self, char: str) -> None:
        if char.isspace() and self.state not in [
           State.READ_KEY.value, State.READ_VALUE.value]:
            return
        match self.state:
            case State.FIND_BRACKET.value:
                if char == '{':
                    self.state = State.WAIT_KEY.value
            case State.WAIT_KEY.value:
                if char == '"':
                    self.buffer = ""
                    self.state = State.READ_KEY.value
            case State.READ_KEY.value:
                if char == '"':
                    self.actual_key = self.buffer
                    self.buffer = ""
                    self.state = State.WAIT_COLON.value
                else:
                    self.buffer += char
            case State.WAIT_COLON.value:
                if char == ':':
                    self.state = State.WAIT_VALUE.value
            case State.WAIT_VALUE.value:
                if not char.isspace():
                    if char == '"':
                        self.state = State.READ_VALUE.value
                        self.tipe_value = "string"
                    elif char.isdigit() or char == '-':
                        self.state = State.READ_VALUE.value
                        self.buffer += char
                        self.tipe_value = "number"
                    else:
                        self.read_dict_value = Parser_llm([])
                        self.read_dict_value.proces_token(char)
                        self.tipe_value = "dic"
                        self.state = State.READ_VALUE.value
            case State.READ_VALUE.value:
                self.__read_value(char)
            case State.WAIT_FINAL_OR_COMMA.value:
                if char == ',':
                    self.state = State.WAIT_KEY.value
                elif char == '}':
                    self.state = State.FINAL.value

    def __read_value(self, char: str) -> None:
        match self.tipe_value:
            case "string":
                if char == '"':
                    value = self.buffer
                    self.__asign_value(value)
                else:
                    self.buffer += char
            case "number":
                if char in (',', '}', ' ', '\t', '\n'):
                    value = self.buffer
                    self.__asign_value(value)
                    self.__trancriptor(char)
                else:
                    self.buffer += char
            case "dic":
                if self.read_dict_value.state == State.FINAL.value:
                    value = self.read_dict_value.stract_data
                    self.__asign_value(value)
                    self.__trancriptor(char)
                else:
                    self.read_dict_value.proces_token(char)

    def __asign_value(self, value: Any) -> None:
        if (self.actual_key in self.objetive_keys or
           len(self.objetive_keys) == 0):
            self.stract_data[self.actual_key] = value
        self.state = State.WAIT_FINAL_OR_COMMA.value
