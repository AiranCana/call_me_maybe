*This project has been created as part of the 42 curriculum by acanadil.*

# call me maybe

Introduction to function calling in LLMs, using **constrained decoding** on a small local model (Qwen3-0.6B).

## Description

### Goal

Large language models understand natural language, but they do not reliably produce machine-executable output. Small models are especially bad at it: asked for JSON, a 0.6B model will often produce something that does not parse.

This project translates a natural-language request into a **structured function call** instead of answering it. Given:

```
"What is the sum of 40 and 2?"
```

the program does **not** answer `42`. It outputs the function to call and its typed arguments:

```json
{
    "prompt": "What is the sum of 40 and 2?",
    "name": "fn_add_numbers",
    "parameters": {"a": 40.0, "b": 2.0}
}
```

The key requirement is that the output is **always valid JSON that follows the schema** in `functions_definition.json`. This is achieved by intervening in the token-by-token generation of the LLM (constrained decoding), not by hoping the model follows a prompt.

### Overview

1. The function definitions and the user prompt are written into a short text prompt.
2. The LLM produces logits for the next token (`Small_LLM_Model.get_logits_from_input_ids`).
3. A hand-written **JSON state machine** (`Parser_llm`) decides which tokens are legal at that exact point of the output.
4. The legal token with the highest logit is appended and the process repeats until the closing `}`.

The function name and the argument values are always **chosen by the LLM** (never by heuristics): the constraints only remove the options that would break the structure or the schema.

### Features

- Constrained decoding driven by a character-level JSON state machine.
- Schema enforcement: key order, function name restricted to the defined functions, per-function `parameters` sub-schema, `number` / `integer` / `string` validation.
- The `"prompt"` field is forced to be an exact copy of the user prompt (including characters that need JSON escaping).
- **Bonus:** own public tokenizer (`Small_llm.tokenizer`) and `Small_llm.decode`, built only from `get_path_to_vocab_file()` and `get_logits_from_input_ids()`. The SDK `encode`/`decode` are never used in the main code.
- Input validation with `pydantic`, graceful error messages, per-prompt error isolation.

## Instructions

### Requirements

- Python 3.10 or later
- [`uv`](https://docs.astral.sh/uv/)
- Dependencies (managed by `uv`, see `pyproject.toml` / `uv.lock`): `numpy`, `pydantic`, `tqdm`, and the local `llm_sdk` package; dev only: `mypy`, `flake8`, `types-tqdm`
- No GPU is needed: everything runs on CPU

### Installation

```bash
make install        # runs `uv sync` (plus the dev type stubs, see below)
```

The Makefile exports `HF_HOME` and `UV_CACHE_DIR` so that the Hugging Face model files and the `uv` cache are stored in a larger, non-home partition (`/goinfre/<login>/`) instead of the quota-limited home directory. If you run the project somewhere else, override them:

```bash
make install HF_HOME=$HOME/.hf-cache UV_CACHE_DIR=$HOME/.uv-cache
```

### Execution

```bash
make run
# equivalent to
uv run python -m src
```

Arguments are forwarded through the `ARGS` variable:

```bash
make run ARGS="--input data/input/function_calling_tests.json --output data/output/out.json"
```

or directly with `uv`:

```bash
uv run python -m src \
    --functions_definition data/input/functions_definition.json \
    --input data/input/function_calling_tests.json \
    --output data/output/function_calling_results.json
```

| Argument | Default |
|---|---|
| `--functions_definition` | `data/input/functions_definition.json` |
| `--input` | `data/input/function_calling_tests.json` |
| `--output` | `data/output/function_calling_results.json` |

The output directory is created automatically if it does not exist.

### Other Makefile rules

| Rule | Description |
|---|---|
| `make install` | `uv sync` (creates the virtual environment and installs the dependencies) |
| `make run [ARGS="..."]` | `uv run python -m src $(ARGS)` |
| `make debug [ARGS="..."]` | `uv run python -m pdb -m src $(ARGS)` (runs the program under `pdb`) |
| `make clean` | Remove every `__pycache__` and `.mypy_cache` |
| `make lint` | `mypy .` with the flags required by the subject, then `flake8 .` (`.venv`, `__pycache__` and `llm_sdk` excluded from `flake8`) |
| `make lint-strict` | `mypy . --strict`, then `flake8 .` |

### Project structure

```
.
├── data/
│   └── input/
│       ├── functions_definition.json
│       └── function_calling_tests.json
├── llm_sdk/                  # provided wrapper around the model
├── src/
│   ├── __init__.py           # exports Small_llm
│   ├── __main__.py           # entry point, output generation
│   ├── parser.py             # CLI arguments + pydantic models for the input files
│   ├── translator.py         # Small_llm: tokenizer, prompt, constrained generation loop
│   ├── state_machine.py      # Parser_llm: JSON state machine (the "oracle")
│   └── enum.py               # State enum
├── pyproject.toml
├── uv.lock
└── README.md
```

## Example usage

**`data/input/functions_definition.json`**

```json
[
  {
    "name": "fn_add_numbers",
    "description": "Add two numbers together and return their sum.",
    "parameters": {"a": {"type": "number"}, "b": {"type": "number"}},
    "returns": {"type": "number"}
  },
  {
    "name": "fn_reverse_string",
    "description": "Reverse a string and return the reversed result.",
    "parameters": {"s": {"type": "string"}},
    "returns": {"type": "string"}
  }
]
```

**`data/input/function_calling_tests.json`**

```json
[
  {"prompt": "What is the sum of 2 and 3?"},
  {"prompt": "Reverse the string 'hello'"}
]
```

**Run**

```bash
$ uv run python -m src
100%|██████████| 2/2 [...]
```

**`data/output/function_calling_results.json`**

```json
[
    {
        "prompt": "What is the sum of 2 and 3?",
        "name": "fn_add_numbers",
        "parameters": {"a": 2.0, "b": 3.0}
    },
    {
        "prompt": "Reverse the string 'hello'",
        "name": "fn_reverse_string",
        "parameters": {"s": "hello"}
    }
]
```

Error handling examples (the program exits with code `1` and a clear message on `stderr`):

```bash
$ uv run python -m src --input missing.json
Error: Bad Input in missing.json

$ uv run python -m src --input broken.json      # invalid JSON
Error: json invalid
```

## Algorithm explanation

### Pipeline

```
prompt ──► tokenizer ──► input ids ──► LLM ──► logits ──► constraints ──► next token
              ▲                                                              │
              └──────────────────── append token and repeat ◄────────────────┘
```

The text given to the model is:

```
System: Output JSON: {"prompt":str (user prompt),"name":str (funtion name),"parameters":obj}.
Functions: [<function definitions as compact JSON>]
User: <user prompt>
Assistant: 
```

The system prompt is only a *hint* that makes the model's logits more useful. Correctness never depends on it: even if the model ignores it completely, the constraints below make the output valid.

### Constrained decoding

At every step:

1. **Logits.** `get_logits_from_input_ids(input_ids)` returns one score per token of the vocabulary (~151k tokens).
2. **Structural forcing.** In states where exactly one character is legal (`{` at the start, `"` before a key, `:` after a key, `,` or `}` after a value), the logit of the matching token is set to `+inf`. This is applied to the top-level parser and to the nested parser that reads `parameters`.
3. **Ranking.** All token ids are sorted by logit, from highest to lowest.
4. **Oracle check.** For each candidate, in order, `Parser_llm.verif_correct_now(token)` is called. It **clones** the state machine (`new_parser`), feeds the decoded token character by character, and accepts the token only if the clone does not end in the `INVALID` state (and the decoded token is not empty).
5. **Commit.** The first accepted token is appended to `input_ids` and fed to the real state machine.
6. The loop ends when the machine reaches `FINAL` (the closing `}` of the top-level object was read).

Rejecting a token is equivalent to setting its logit to `-inf`, but it is done lazily: only the candidates better than the first valid one are ever checked. The selection is greedy (arg-max over the valid tokens).

### The state machine (`Parser_llm`)

`Parser_llm` is a character-level finite-state machine with these states:

```
FIND_BRACKET → WAIT_KEY → READ_KEY → WAIT_COLON → WAIT_VALUE → READ_VALUE → WAIT_FINAL_OR_COMMA → FINAL
                  ▲                                                               │
                  └───────────────────────── "," (keys left) ◄────────────────────┘
                                         any violation → INVALID
```

The schema is injected as an ordered dictionary of `key → type`:

- **Top level:** `{"prompt": "string", "name": "string", "parameters": "dic"}`. Keys must appear in exactly this order, and a key is checked as a prefix while it is being written, so a wrong key is rejected at the first wrong character.
- **`name`:** while it is written, the buffer must always be a prefix of at least one defined function name, and it can only be closed if it equals one of them. The LLM therefore *chooses* among real functions only.
- **`prompt`:** the buffer must always be a prefix of the **JSON-escaped** user prompt (`json.dumps(prompt)[1:-1]`) and it can only be closed when it is equal to it. Escaping first matters: a prompt containing `"` or `\` has to be written as `\"` / `\\` in JSON.
- **`parameters`:** when `{` is read, a **second `Parser_llm`** is created with the sub-schema of the function already chosen (`{"a": "number", "b": "number"}`, etc.). From then on, every character is delegated to it until it reaches `FINAL`. Because the function name is read before `parameters`, the model can only emit the keys of that function, in order, with values of the declared type.
- **Values:** `number` accepts `-`, digits and a single `.`, and is validated with `float()`; `integer` accepts digits and is validated with `int()`; `string` is read until an unescaped `"`. Every assigned value is round-tripped through `json.loads` before being accepted.
- **Whitespace** is ignored between structural elements and significant only inside keys and values.

Since the machine can be cloned, it also works as a *what-if* oracle: "if this token were appended, would the output still be valid?"

### Tokenizer (bonus)

The vocabulary file returned by `get_path_to_vocab_file()` is a flat `token → id` JSON using GPT-2-style byte-level BPE (`Ġ` = space, `Ċ` = newline). `Small_llm` implements its own:

- `tokenizer(text) -> list[int]`: converts the text to UTF-8 bytes, maps each byte to the printable GPT-2 unicode alphabet (`bytes_to_unicode`), and then applies a **greedy longest-match** against the vocabulary.
- `decode(ids) -> str`: concatenates the token strings, maps the characters back to bytes and decodes as UTF-8.

The merge rules are not available, so the greedy longest-match is an *approximation* of the real BPE segmentation. It is used both to encode the prompt and to find the ids of the structural tokens (`{`, `"`, `:`, `,`, `}`), and `decode` is what lets the state machine "read" a candidate token. The SDK's `encode`/`decode` are not used and no private SDK attribute is touched.

## Design decisions

- **Character-level state machine instead of a regex/grammar library.** Libraries such as `outlines` are forbidden, and a hand-written machine makes it easy to attach *semantic* rules (name must be a defined function, prompt must be a copy of the input) to the syntactic ones.
- **Validate by simulation (clone + feed) instead of precomputing masks.** Tokens are multi-character, so the legality of a token depends on every character it contains. Cloning the machine and feeding the token reuses exactly the same logic that later commits the token, so there is a single source of truth.
- **Two-level parser for `parameters`.** The sub-schema depends on the function name chosen earlier, so the nested object is parsed by a child `Parser_llm` created at that moment. This also keeps the design open to deeper nesting.
- **`+inf` forcing for punctuation, rejection for everything else.** Forcing the single legal punctuation token avoids a long scan over the vocabulary in the places where there is no real choice.
- **The prompt field is copied under constraint rather than inserted.** The LLM still emits those tokens (the constraint only restricts them to the prefix of the real prompt), so the generation stays a model-driven process and not a string substitution.
- **Numbers are emitted as floats** (`2.0`, `3.0`), as in the output example of the subject.
- **Greedy selection.** Deterministic output makes the results reproducible and easier to test.
- **`pydantic` for every input/output model** (`Funtions`, `TypeSpec`, `Prompts`, `Output`), as required by the subject.
- **Failures are isolated per prompt:** if generation fails for one prompt, an error is printed and the remaining prompts are still processed.

## Performance analysis

- **Reliability.** Structure is enforced by construction: every committed token has been accepted by the state machine, so the produced string is syntactically valid JSON and matches the schema (key order, function name, parameter names and types). `main` additionally validates each result with `pydantic` before writing it, and parses it with `json.loads`.
- **Accuracy.** Function selection and argument extraction are done by the LLM, so accuracy depends on the model and on the prompt. Since the choice is restricted to real function names and keys, the typical failure mode is *choosing a plausible but wrong function* or *copying a wrong value*, never producing malformed output.
- **Speed.** Measured on an Intel Mac, CPU only (no CUDA, no MPS): about **7 min 15 s for 11 prompts** at the time of the last measurement, above the 5-minute target of the subject. The main costs are:
  - one full forward pass per generated token (the SDK method receives the full id list; whether it reuses a KV cache between calls has to be confirmed);
  - sorting the ~151k logits at every step;
  - decoding and simulating many candidate tokens when the model's favourite tokens are invalid (typical inside `prompt`, where almost everything the model wants to say is rejected).
- **Ideas to go faster.**
  - Build a prefix mask over the vocabulary against the *remaining* text of `prompt` / `name` instead of testing candidates one by one, which also allows multi-character BPE tokens to be accepted directly.
  - Apply the same prefix filtering to the digits of `number` values.
  - Replace the full sort by a partial selection (`numpy.argpartition` / iterating only the top-k) and cache `decode` results per token id.
  - Reuse the KV cache between steps if the SDK allows it.

## Challenges faced

Most of the work was making the state machine tight enough that *no* illegal output exists, and loose enough that *every* legal output is reachable:

1. **Infinite whitespace loops.** Whitespace was a no-op for the parser (it never changes the state), so it was never `INVALID` and the model could generate spaces and newlines until `max_tokens`. Fixed by forcing the legal punctuation in every state where only one character is valid, including inside the nested `parameters` parser (the logit forcing originally looked only at the top-level state).
2. **Tokens that decode to an empty string.** Special ids that are not in the flat vocabulary decode to `""`; since `for char in ""` never runs, the cloned machine stayed in a valid state and the token was accepted without any check. Fixed with an explicit `len(token) != 0` check in `verif_correct_now`.
3. **`prompt` never closing / never matching.** The comparison of the `prompt` value against the real prompt had the wrong polarity (`is not None` instead of `is None`), so the check never ran. Afterwards, using `.strip(" ")` in the prefix check let extra spaces accumulate until the exact-equality check at the closing quote failed. Fixed by comparing the buffer against the prompt exactly, character by character.
4. **Escaping.** Prompts containing `"` or `\` (for instance a regular expression such as `\d+`) cannot be matched against the raw prompt, because the generated JSON has to contain the escaped version. Fixed by comparing against `json.dumps(prompt)[1:-1]`. As a safety net, `__string_to_json` in `__main__.py` doubles any backslash that is not a valid JSON escape before a second `json.loads` attempt.
5. **Numbers never closing.** The validation of a value built the JSON snippet assuming a string, so for numeric values it raised an unbound-variable error, fell into `INVALID` and the parser could only keep appending digits. Fixed by validating through `json.loads(json.dumps({key: value}))`.
6. **`list index out of range` with two or more parameters.** After the last key the parser still accepted `,` and tried to read a key that did not exist. Fixed by only accepting `,` while `len(stract_data) < len(dis_key)` and `}` otherwise.
7. **Logit forcing replaced the whole vector.** A list comprehension iterated over the *values* of the logits instead of the indices (and compared them with lists of ids), turning the whole vector into `-inf`. Fixed with direct index assignment on the cached punctuation ids.
8. **Tokenizer without merges.** Only the flat vocabulary is available, so BPE merges cannot be replayed; the tokenizer uses greedy longest-match as an approximation.

## Testing strategy

- **Subject examples first:** the sample `functions_definition.json` and `function_calling_tests.json` (sum, greet, reverse string, ...), checking `name`, argument names and argument types in the output.
- **Edge cases** listed in the subject, run one by one while reading the generation trace:
  - empty strings and strings with special characters (quotes, backslashes, regular expressions);
  - large and negative numbers, numbers with decimals;
  - functions with several parameters, in particular the case where the last key has just been closed;
  - ambiguous prompts that could match several functions;
  - function names that share a prefix.
- **Output validation:** every result is validated with `pydantic` (`Output`) and `json.loads`; the final file is checked to be valid JSON, to contain exactly the keys `prompt`, `name`, `parameters`, and to have types that match the function definition.
- **Input robustness:** missing files, wrong extension, empty file, invalid JSON, and JSON with a wrong structure must produce a clear message on `stderr` and exit code `1`, never a traceback.
- **Static checks:** `make lint` (`flake8` + `mypy` with the flags of the subject).
- **Regression approach:** each bug listed in *Challenges faced* was reproduced with the smallest prompt that triggered it and re-run after the fix.

## Known limitations

- `boolean` is accepted by the input schema (`TypeSpec`) but the generation state machine currently only produces `string`, `number` and `integer` values.
- `integer` values are stored as floats in the result (`3.0`).
- Only one level of nesting is supported (`parameters` as a flat object).
- The tokenizer is a greedy approximation of byte-level BPE (no merge rules available).
- Speed on CPU is above the 5-minute target for large test sets (see *Performance analysis*).

## Resources

### References

- Subject of the project: *call me maybe — Introduction to function calling in LLMs* (42 curriculum).
- Qwen3 model card: <https://huggingface.co/Qwen/Qwen3-0.6B>
- Radford et al., *Language Models are Unsupervised Multitask Learners* (GPT-2, byte-level BPE and the `bytes_to_unicode` table).
- Sennrich et al., *Neural Machine Translation of Rare Words with Subword Units* (BPE), 2016.
- Willard & Louf, *Efficient Guided Generation for Large Language Models* (finite-state-machine guided decoding), 2023.
- JSON specification, RFC 8259: <https://datatracker.ietf.org/doc/html/rfc8259>
- Python documentation: `json`, `argparse`, `pathlib`, `typing`; `pydantic` documentation; `uv` documentation.

### Use of AI

AI assistants were used as a **review and debugging aid**, never as a replacement for understanding the code:

- **Debugging the state machine and the generation loop:** analysing traces where the generation got stuck (whitespace loops, `prompt` not closing, numbers not closing, wrong escaping, `index out of range`, logits overwritten) and discussing possible root causes. Every fix was implemented, tested and understood by me before being kept.
- **Design discussion:** comparing alternatives for the oracle (prefix masks over the vocabulary vs. testing candidates one by one) and for the tokenizer.

The function-calling logic, the state machine, the tokenizer and the generation loop were written by me.