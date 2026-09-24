
from llm_sdk import Small_LLM_Model
from typing import Any
from pathlib import Path
from src.enum import State
from src.state_machine import Parser_llm
import json

dicts: dict[str, str] = {
    "prompt": "string",
    "name": "string",
    "parameters": "dic"
}


class Small_llm:
    def __init__(self, functions: list[dict[str, Any]]) -> None:
        self.__device = "cpu"
        self.parameters = {
            funtion["name"]: {
                k: v.type for k, v in funtion["parameters"].items()
            } for funtion in functions
        }
        self.generate_sys_prompt(functions)
        try:
            self.generate_model()
        except Exception as e:
            raise ValueError(e)

    def generate_model(self):
        self.__encoder = self.__bytes_to_unicode()
        self.__decoder = {k: v for v, k in self.__encoder.items()}
        self.model = Small_LLM_Model(device=self.__device)
        self.dic_ecoder: dict[str, int] = json.loads(
                Path(self.model.get_path_to_vocab_file())
                .read_text(encoding="utf-8"))
        self.dic_decoder = {item: key
                            for key, item in self.dic_ecoder.items()}
        self.unk_id = self.dic_ecoder.get("<unk>", 0)
        self.max_token_len = (max(
                len(key) for key in self.dic_ecoder.keys())
                if self.dic_ecoder else 1)
        self.generate_special_tokens()

    def generate_special_tokens(self) -> None:
        self._id_open_bracket = self.tokenizer("{")[0]
        self._id_quote = self.tokenizer('"')[0]
        self._id_colon = self.tokenizer(":")[0]
        self._id_comma = self.tokenizer(",")[0]
        self._id_close_brace = self.tokenizer("}")[0]

    def generate_sys_prompt(self, functions: list[dict[str, Any]]) -> None:
        for x in functions:
            x["returns"] = x["returns"].__dict__
            for key, val in x["parameters"].items():
                x["parameters"][key] = val.__dict__
        functions_text = json.dumps(functions, indent=2)
        self.sys_prom = ('System: '
                         "You are a function calling assistant. "
                         "You will give a json with this stile: "
                         '{"prompt": "user_prompt", "name": "funtion_name",'
                         ' "parameters": value}'
                         "The functions "
                         "that you have are: <tools>" + functions_text +
                         "</tools>")

    def __bytes_to_unicode(self) -> dict[int, str]:
        bas = (list(range(ord("!"), ord("~") + 1)) +
               list(range(ord("¡"), ord("¬") + 1)) +
               list(range(ord("®"), ord("ÿ") + 1)))
        cast = bas[:]
        n = 0
        for b in range(256):
            if b not in bas:
                bas.append(b)
                cast.append(256 + n)
                n += 1
        return dict(zip(bas, [chr(c) for c in cast]))

    def generator(self, prompt: str,
                  prompt_base: str, max_tokens: int = 400) -> str:
        input_ids = self.tokenizer(prompt)
        escaped_prompt_base = json.dumps(prompt_base)[1:-1]
        result = []
        generated_tokens = 0
        machine = Parser_llm(dicts, self.parameters)
        tok = 0
        while True:
            next_token_posi = self.get_next_posible_tokens(input_ids, machine)
            if machine.state == State.FINAL:
                break
            logits = sorted(range(len(next_token_posi)),
                            key=lambda idx: next_token_posi[idx],
                            reverse=True)
            found = False
            for next_token in logits:
                if machine.verif_correct_now(self.decode([next_token]),
                                             escaped_prompt_base):
                    machine.proces_token(self.decode([next_token]),
                                         escaped_prompt_base)
                    input_ids.append(next_token)
                    result.append(next_token)
                    generated_tokens += 1
                    eos_token = self.dic_ecoder.get("</s>")
                    found = True
                    tok += 1
                    break
            if not found:
                print("Error: Can't predict next token")
                exit(1)
            if next_token == eos_token:
                break
            if generated_tokens >= max_tokens:
                break
        print(tok)
        return self.decode(result)

    def get_next_posible_tokens(
            self,
            input_ids: list[int],
            machine: Parser_llm
            ) -> list[float]:
        proces_next_token = self.model.get_logits_from_input_ids(input_ids)
        if machine.state == State.FIND_BRACKET:
            proces_next_token[self._id_open_bracket] = float("inf")
        if machine.state == State.WAIT_KEY:
            proces_next_token[self._id_quote] = float("inf")
        if machine.state == State.WAIT_COLON:
            proces_next_token[self._id_colon] = float("inf")
        if (n := machine.read_dict_value) is not None:
            if n.state == State.FIND_BRACKET:
                proces_next_token[self._id_open_bracket] = float("inf")
            if n.state == State.WAIT_KEY:
                proces_next_token[self._id_quote] = float("inf")
            if n.state == State.WAIT_COLON:
                proces_next_token[self._id_colon] = float("inf")
            if n.state == State.WAIT_FINAL_OR_COMMA:
                if len(n.stract_data) < len(n.dis_key):
                    proces_next_token[self._id_comma] = float("inf")
                else:
                    proces_next_token[self._id_close_brace] = float("inf")
        if machine.state == State.WAIT_FINAL_OR_COMMA:
            if len(machine.stract_data) < len(machine.dis_key):
                proces_next_token[self._id_comma] = float("inf")
            else:
                proces_next_token[self._id_close_brace] = float("inf")
        return proces_next_token

    def __transformer(self, prompt: str) -> str:
        prom_bytes = prompt.encode("utf-8")
        return "".join(self.__encoder[b] for b in prom_bytes)

    def tokenizer(self, prompt: str) -> list[int]:
        inputs_id = []
        prompt = self.__transformer(prompt)
        i = 0
        n = len(prompt)
        while i < n:
            match_found = False
            max_len = min(n - i, self.max_token_len)

            for leng in range(max_len, 0, -1):
                sub_str = prompt[i: i + leng]
                if sub_str in self.dic_ecoder:
                    inputs_id.append(self.dic_ecoder[sub_str])
                    i += leng
                    match_found = True
                    break
            if not match_found:
                inputs_id.append(self.unk_id)
                i += 1
        return inputs_id

    def decode(self, tokens: list[int]) -> str:
        out_byte = "".join(self.dic_decoder.get(tok, "") for tok in tokens)
        text = bytes(self.__decoder[ch] for ch in out_byte
                     if ch in self.__decoder)
        return text.decode("utf-8", errors="replace")

    def communication(self, prompt: str) -> str:
        new_prompt = "\nUser: " + prompt + "\nAssistant: "
        return self.generator(self.sys_prom + new_prompt, prompt)
