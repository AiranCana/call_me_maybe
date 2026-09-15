
from llm_sdk import Small_LLM_Model
import torch
import json
from pathlib import Path


class Small_llm:
    def __init__(self) -> None:
        self.__device = "cpu"
        try:
            self.__encoder = self.__bytes_to_unicode()
            self.__decoder = {k: v for v, k in self.__encoder.items()}
            self.model = Small_LLM_Model(device="cpu")
            self.dic_ecoder: dict[str, int] = json.loads(
                Path(self.model.get_path_to_vocab_file())
                .read_text(encoding="utf-8"))
            print(self.model.get_path_to_vocab_file())
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

    def communication(self, prompt: str, max_tokens: int = 400
                      ) -> str:
        input_ids = self.tokenizer(prompt)
        result = []
        generated_tokens = 0
        while True:
            logits = self.model.get_logits_from_input_ids(input_ids)
            logits_tensor = torch.tensor(logits)

            self.apply_repetition_penalty(logits_tensor, input_ids)
            next_token = self.aleatorety(logits_tensor)
            input_ids.append(next_token)
            result.append(next_token)
            generated_tokens += 1
            eos_token = self.dic_ecoder.get("</s>")
            if next_token == eos_token:
                break
            if generated_tokens >= max_tokens:
                break
        return self.decode(result)

    def aleatorety(self, logits: torch.Tensor, temerature: float = 0.8) -> int:
        scale = logits / temerature
        prob = torch.softmax(scale, dim=-1)
        return int(torch.multinomial(prob, num_samples=1).item())

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

    def apply_repetition_penalty(
            self, logits: torch.Tensor,
            input_ids: list[int],
            penalty: float = 1.2) -> torch.Tensor:
        for token_id in set(input_ids):
            if logits[token_id] > 0:
                logits[token_id] /= penalty
            else:
                logits[token_id] *= penalty
        return logits


if __name__ == "__main__":
    prompt = "What is the sum of 2 and 2?"
    hola = Small_llm()
    response = hola.communication(prompt)
    print(response)
