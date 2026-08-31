
import llm_sdk
import torch


def communication(prompt: str) -> str:
    model = llm_sdk.Small_LLM_Model(model_name="gpt2", device="cpu", dtype=None, trust_remote_code=True)
    input_ids = tokenizer(prompt, model)
    max_new_tokens = 50
    for _ in range(max_new_tokens):
        # Obtener logits
        logits = model.get_logits_from_input_ids(input_ids)

        # Seleccionar el siguiente token (greedy decoding o sampling)
        next_token_logits = logits[:, -1, :]
        next_token = torch.argmax(next_token_logits, dim=-1, keepdim=True)

        # Añadir al historial de tokens
        input_ids = torch.cat([input_ids, next_token], dim=-1)

        # Detener si se genera fin de secuencia (EOT token de GPT-2 es 50256)
        if next_token.item() == 50256:
            break
    return decode(input_ids, model)


def tokenizer(prompt: str, model: llm_sdk.Small_LLM_Model) -> list[str]:
    input_ids = model.encode(prompt)
    if isinstance(input_ids, list):
        input_ids = torch.tensor([input_ids])
    return input_ids


def decode(tokens: list[str], model: llm_sdk.Small_LLM_Model) -> str:
    return model.decode(tokens[0].tolist())


if __name__ == "__main__":
    prompt = "Hello, world!"
    response = communication(prompt)
    print(response)
