from src.enum import State
from typing import Any
import json


class Parser_llm:

    def __init__(self, objetive_keys: dict[str, str],
                 parameters: dict[str, dict[str, str]] = {}):
        self.objetive_keys = objetive_keys
        self.dis_key = [key for key in objetive_keys.keys()]
        self.parameters = parameters
        self.state = State.FIND_BRACKET
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
           State.READ_KEY, State.READ_VALUE]:
            return
        match self.state:
            case State.FIND_BRACKET:
                if char == '{':
                    self.state = State.WAIT_KEY
                else:
                    self.state = State.INVALID
            case State.WAIT_KEY:
                if char == '"':
                    self.buffer = ""
                    self.state = State.READ_KEY
                else:
                    self.state = State.INVALID
            case State.READ_KEY:
                if char == '"':
                    if self.buffer in self.objetive_keys.keys():
                        if self.buffer == self.dis_key[
                           len(self.stract_data)]:
                            self.actual_key = self.buffer
                            self.state = State.WAIT_COLON
                            self.tipe_value = self.objetive_keys[
                                self.actual_key]
                        else:
                            self.state = State.INVALID
                    else:
                        self.state = State.INVALID
                    self.buffer = ""
                else:
                    self.buffer += char
                    if not (self.dis_key[len(self.stract_data)].
                       startswith(self.buffer)):
                        self.state = State.INVALID
            case State.WAIT_COLON:
                if char == ':':
                    self.state = State.WAIT_VALUE
                else:
                    self.state = State.INVALID
            case State.WAIT_VALUE:
                if char == '"' and self.tipe_value == "string":
                    self.state = State.READ_VALUE
                elif ((char.isdigit() or char == '-') and
                      self.tipe_value == "number"):
                    self.state = State.READ_VALUE
                    self.buffer += char
                elif char == "{" and self.tipe_value == "dic":
                    if (n := self.stract_data.get("name", None)) is None:
                        self.state = State.INVALID
                    elif n not in self.parameters.keys():
                        self.state = State.INVALID
                    else:
                        self.read_dict_value = Parser_llm(
                            self.parameters[n])
                        self.read_dict_value.proces_token(char)
                        self.state = State.READ_VALUE
                else:
                    self.state = State.INVALID
            case State.READ_VALUE:
                self.__read_value(char)
            case State.WAIT_FINAL_OR_COMMA:
                if char == ',':
                    self.state = State.WAIT_KEY
                elif char == '}':
                    self.state = State.FINAL
                else:
                    self.state = State.INVALID

    def __read_value(self, char: str) -> None:
        match self.tipe_value:
            case "string":
                if char == '"' and not self.buffer.endswith("\\"):
                    value = self.buffer
                    if (self.stract_data.get("name", None) is None and
                       self.actual_key == "name"):
                        if len(self.parameters) != 0:
                            if any(x == self.buffer for x in self.
                                   parameters.keys()):
                                self.__asign_value(value)
                            else:
                                self.state = State.INVALID
                        else:
                            self.__asign_value(value)
                    else:
                        self.__asign_value(value)
                else:
                    if (self.stract_data.get("name", None) is None and
                       self.actual_key == "name"):
                        if len(self.parameters) != 0:
                            if any(x.startswith(
                                self.buffer + char) for x in self.
                                   parameters.keys()):
                                self.buffer += char
                            else:
                                self.state = State.INVALID
                        else:
                            self.buffer += char
                    else:
                        self.buffer += char
            case "number":
                if char in (',', '}', ' ', '\t', '\n'):
                    try:
                        float(self.buffer)
                        value = self.buffer
                    except ValueError:
                        self.state = State.INVALID
                        return
                    self.__asign_value(float(value))
                    self.__trancriptor(char)
                else:
                    if char in "0123456789.":
                        if ((char == "." and self.buffer.find(".") + 1) or
                           (char == "." and self.buffer == "")):
                            self.state = State.INVALID
                        else:
                            self.buffer += char
                    else:
                        self.state = State.INVALID
            case "dic":
                if self.read_dict_value.state == State.FINAL:
                    value = self.read_dict_value.stract_data
                    self.__asign_value(value)
                    self.__trancriptor(char)
                else:
                    self.read_dict_value.proces_token(char)
                    if self.read_dict_value.state == State.INVALID:
                        self.state = State.INVALID

    def __asign_value(self, value: Any) -> None:
        try:
            json.loads("{" + f"{self.actual_key}: {value}" + "}")
        except Exception:
            self.state = State.INVALID
            return
        if (self.actual_key in self.objetive_keys or
           len(self.objetive_keys) == 0):
            self.stract_data[self.actual_key] = value
        self.state = State.WAIT_FINAL_OR_COMMA

    def new_parser(self) -> "Parser_llm":
        news = Parser_llm(self.objetive_keys, self.parameters)
        news.buffer = self.buffer
        news.state = self.state
        news.actual_key = self.actual_key
        news.stract_data = self.stract_data.copy()
        news.tipe_value = self.tipe_value
        if self.read_dict_value is not None:
            news.read_dict_value = self.read_dict_value.new_parser()
        return news

    def verif_correct_now(self, token: str) -> bool:
        pruber = self.new_parser()
        pruber.proces_token(token)
        return pruber.state != State.INVALID and len(token) != 0
