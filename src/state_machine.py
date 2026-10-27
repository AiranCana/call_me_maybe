from src.enum import State
from typing import Any, Optional
import json


class Parser_llm:
    """Stream model output through a JSON state machine.

    The parser validates tokens as they arrive and keeps only values that fit
    the expected schema for the function-call response.
    """

    def __init__(self, objetive_keys: dict[str, str],
                 parameters: dict[str, dict[str, str]] = {}):
        """Initialize the parser state machine.

        Args:
            objetive_keys: Expected JSON fields and their data types.
            parameters: Nested parameter definitions for dictionary-valued
                fields.
        """

        self.objetive_keys = objetive_keys
        self.dis_key = [key for key in objetive_keys.keys()]
        self.parameters = parameters
        self.state = State.FIND_BRACKET
        self.buffer = ""
        self.actual_key = ""
        self.stract_data: dict[str, Any] = {}
        self.tipe_value = ""
        self.read_dict_value: Optional[Parser_llm] = None

    def proces_token(self, token: str, prompt: str) -> None:
        """Process one or more output characters from the model.

        Args:
            token: Incoming token text to validate.
            prompt: Original user prompt used to match prompt field values.
        """

        for char in token:
            self.__trancriptor(char, prompt)

    def __trancriptor(self, char: str, prompt: str) -> None:
        """Route a single character through the active parser state."""

        if char.isspace() and self.state not in [
           State.READ_KEY, State.READ_VALUE]:
            return
        match self.state:
            case State.FIND_BRACKET:
                self.__wait_one_thing(char, "{", State.WAIT_KEY)
            case State.WAIT_KEY:
                if char == '"':
                    self.buffer = ""
                    self.state = State.READ_KEY
                else:
                    self.state = State.INVALID
            case State.READ_KEY:
                self.__read_key(char)
            case State.WAIT_COLON:
                self.__wait_one_thing(char, ":", State.WAIT_VALUE)
            case State.WAIT_VALUE:
                self.__wait_value(char, prompt)
            case State.READ_VALUE:
                self.__read_value(char, prompt)
            case State.WAIT_FINAL_OR_COMMA:
                if char == ',' and len(self.stract_data) < len(self.dis_key):
                    self.state = State.WAIT_KEY
                else:
                    self.__wait_one_thing(char, "}", State.FINAL)
            case State.FINAL:
                self.state = State.INVALID

    def __wait_one_thing(self, char: str, thing: str, value: State) -> None:
        """Validate that the next character matches an expected delimiter."""

        if char == thing:
            self.state = value
        else:
            self.state = State.INVALID

    def __wait_value(self, char: str, prompt: str) -> None:
        """Handle a value that is expected but not yet being read."""

        if (char == 't' or char == 'f') and self.tipe_value == "boolean":
            self.state = State.READ_VALUE
            self.buffer += char
        elif char == '"' and self.tipe_value == "string":
            self.state = State.READ_VALUE
        elif ((char.isdigit() or char == '-') and
              self.tipe_value == "number"):
            self.state = State.READ_VALUE
            self.buffer += char
        elif ((char.isdigit() or char == '-') and
              self.tipe_value == "integer"):
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
                self.read_dict_value.proces_token(char, prompt)
                self.state = State.READ_VALUE
        else:
            self.state = State.INVALID

    def __read_key(self, char: str) -> None:
        """Read and validate a JSON object key against the expected schema."""

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

    def __read_value(self, char: str, prompt: str) -> None:
        """Read the value for the current field based on its declared type."""

        match self.tipe_value:
            case "string":
                self.__read_value_str(char, prompt)
            case "number":
                return self.__read_value_num(char, prompt, "number")
            case "integer":
                return self.__read_value_num(char, prompt, "integer")
            case "dic":
                if (self.read_dict_value is not None and
                   self.read_dict_value.state == State.FINAL):
                    value = self.read_dict_value.stract_data
                    self.__asign_value(value)
                    self.__trancriptor(char, prompt)
                elif self.read_dict_value is not None:
                    self.read_dict_value.proces_token(char, prompt)
                    if self.read_dict_value.state == State.INVALID:
                        self.state = State.INVALID
            case "boolean":
                target = "true" if self.buffer[0] == "t" else "false"
                if self.buffer + char in ["true", "false"]:
                    self.buffer += char
                    self.__asign_value(self.buffer == "true")
                elif not target.startswith(self.buffer + char):
                    self.state = State.INVALID
                else:
                    self.buffer += char

    def __read_value_num(self, char: str, prompt: str,
                         value_type: str) -> None:
        """Parse a numeric JSON value and validate it against the shape."""

        value: int | float
        if char in (',', '}', ' ', '\t', '\n'):
            try:
                if value_type == "integer":
                    value = int(self.buffer)
                elif self.buffer.find(".") + 1 != 0:
                    value = float(self.buffer)
                else:
                    raise ValueError
            except ValueError:
                self.state = State.INVALID
                return
            self.__asign_value(float(value))
            self.__trancriptor(char, prompt)
        else:
            permit = "0123456789"
            if value_type == "number":
                permit += "."
            if char in permit:
                if ((char == "." and self.buffer.find(".") + 1) or
                   (char == "." and self.buffer == "")):
                    self.state = State.INVALID
                else:
                    self.buffer += char
            else:
                self.state = State.INVALID

    def __read_value_str(self, char: str, prompt: str) -> None:
        """Parse a string field one character at a time."""

        if char == '"' and not self.buffer.endswith("\\"):
            self.__finish_read_value_str(prompt)
        else:
            self.__continue_read_value_str(char, prompt)

    def __continue_read_value_str(self, char: str, prompt: str) -> None:
        """Extend the current string buffer while checking allowed values."""

        if (self.stract_data.get("name", None) is None and
           self.actual_key == "name"):
            if len(self.parameters) != 0:
                if any(x.startswith(
                         self.buffer + char) for x in self.parameters.keys()):
                    self.buffer += char
                else:
                    self.state = State.INVALID
            else:
                self.buffer += char
        elif (self.stract_data.get("prompt", None) is None and
              self.actual_key == "prompt"):
            if prompt.startswith((self.buffer + char)):
                self.buffer += char
            else:
                self.state = State.INVALID
        else:
            self.buffer += char

    def __finish_read_value_str(self, prompt: str) -> None:
        """Finalize a string value while validating names and prompts."""

        value = self.buffer
        if (self.stract_data.get("name", None) is None and
           self.actual_key == "name"):
            if len(self.parameters) != 0:
                if any(x == self.buffer for x in self.parameters.keys()):
                    self.__asign_value(value)
                else:
                    self.state = State.INVALID
            else:
                self.__asign_value(value)
        elif (self.stract_data.get("prompt", None) is None and
              self.actual_key == "prompt"):
            if (self.buffer == prompt):
                self.__asign_value(value)
            else:
                self.state = State.INVALID
        else:
            self.__asign_value(value)

    def __asign_value(self, value: Any) -> None:
        """Persist a validated field value into the parsed result tree."""

        if isinstance(value, str):
            value2 = f'"{value}"'
        else:
            value2 = value
        text = json.dumps({self.actual_key: value2})
        try:
            json.loads(text)
        except Exception:
            self.state = State.INVALID
            return
        if (self.actual_key in self.objetive_keys or
           len(self.objetive_keys) == 0):
            self.stract_data[self.actual_key] = value
        self.state = State.WAIT_FINAL_OR_COMMA

    def new_parser(self) -> "Parser_llm":
        """Create a cloned parser state for a next-token validity check.

        Returns:
            Parser_llm: A snapshot that shares the current parser schema.
        """

        news = Parser_llm(self.objetive_keys, self.parameters)
        news.buffer = self.buffer
        news.state = self.state
        news.actual_key = self.actual_key
        news.stract_data = self.stract_data.copy()
        news.tipe_value = self.tipe_value
        if self.read_dict_value is not None:
            news.read_dict_value = self.read_dict_value.new_parser()
        return news

    def verif_correct_now(self, token: str, prompt: str) -> bool:
        """Check whether a candidate token could still lead to valid output.

        Args:
            token: Candidate token text to test.
            prompt: User prompt used during prompt matching.

        Returns:
            bool: True when the token keeps the parse valid, otherwise False.
        """

        pruber = self.new_parser()
        pruber.proces_token(token, prompt)
        return pruber.state != State.INVALID and len(token) != 0
