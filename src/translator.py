
from llm_sdk import Small_LLM_Model
from torch import Tensor, tensor
from typing import cast


def communication(prompt: str, max_tokens: int = 400) -> str | list[str]:
    model = Small_LLM_Model(model_name="gpt2", device="cpu")
    input_ids = tokenizer(prompt, model)
    print(f"\n{model.get_path_to_vocab_file()}", end="\n\n")
    generated_tokens = 0
    while True:
        logits = model.get_logits_from_input_ids(input_ids)
        logits_tensor = tensor(logits)

        apply_repetition_penalty(logits_tensor, input_ids)
        next_token = int(logits_tensor.argmax().item())
        generated_tokens += 1
        if next_token == 50256:
            break
        if generated_tokens >= max_tokens:
            break
    input_ids.append(next_token)
    return decode(input_ids, model)


def tokenizer(prompt: str, model: Small_LLM_Model) -> list[int]:
    return list(model._tokenizer.encode(prompt, add_special_tokens=False))


def decode(tokens: list[int], model: Small_LLM_Model) -> str:
    return cast(str, model._tokenizer.decode(tokens, skip_special_tokens=True))


def apply_repetition_penalty(logits: Tensor, input_ids: list[int],
                             penalty: float = 1.2) -> Tensor:
    for token_id in set(input_ids):
        if logits[token_id] > 0:
            logits[token_id] /= penalty
        else:
            logits[token_id] *= penalty
    return logits


if __name__ == "__main__":
    prompt = "What is the sum of 2 and 2?"
    response = communication(prompt)
    print(response)
