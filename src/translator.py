
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
    def __init__(self) -> None:
        self.__device = "cpu"
        try:
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
        except Exception as e:
            raise ValueError(e)

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

    def generator(self, prompt: str, parameters: dict[str, dict[str, str]],
                  max_tokens: int = 400) -> str:
        input_ids = self.tokenizer(prompt)
        result = []
        generated_tokens = 0
        machine = Parser_llm(dicts, parameters)
        while True:
            proces_next_token = self.model.get_logits_from_input_ids(input_ids)
            if machine.state == State.FIND_BRACKET:
                proces_next_token[self.tokenizer("{")[0]] = float("inf")
            if machine.state == State.WAIT_KEY:
                proces_next_token[self.tokenizer('"')[0]] = float("inf")
            if machine.state == State.WAIT_COLON:
                proces_next_token[self.tokenizer(':')[0]] = float("inf")
            if machine.state == State.WAIT_VALUE:
                pass
            if machine.state == State.WAIT_FINAL_OR_COMMA:
                pass
            if machine.state == State.FINAL:
                break
            logits = sorted(range(len(proces_next_token)),
                            key=lambda idx: logits[idx],
                            reverse=True)
            for next_token in logits:
                if machine.verif_correct_now(self.decode([next_token])):
                    print(self.decode([next_token]))
                    machine.proces_token(self.decode([next_token]))
                    input_ids.append(next_token)
                    result.append(next_token)
                    generated_tokens += 1
                    eos_token = self.dic_ecoder.get("</s>")
                    break
            if next_token == eos_token:
                break
            if generated_tokens >= max_tokens:
                break
        return self.decode(result)

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

    def communication(self, functions: list[dict[str, Any]],
                      prompt: str) -> str:
        parameters = {
            key["name"]: {
                k: v["type"] for k, v in key["parameters"].items()
            } for key in functions
        }
        functions_text = json.dumps(functions, indent=2)
        sys_prom = ("System: "
                    "You are a function calling assistant. "
                    "You will give a json with this parameters: "
                    "prompt (that is the prompt of user, is the same rpompt,"
                    " letter for letter), "
                    "name (the name of function), "
                    "parameters (the parameters of the function). "
                    "For example: "
                    '{"prompt":"What is the sum of 2 and 3?","name":'
                    '"fn_add_numbers","parameters":{"a":2.0,"b":3.0}} '
                    "The functions "
                    "that you have are: " + functions_text)
        new_prompt = "\nUser: " + prompt + "\nAssistant: "
        return self.generator(sys_prom + new_prompt, parameters)
