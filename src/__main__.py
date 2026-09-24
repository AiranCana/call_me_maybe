import sys
from pathlib import Path
from pydantic import ValidationError
from typing import Any
import json
from tqdm import tqdm
from src import Small_llm
from src.parser import parser, Output


def main() -> int:
    try:
        datas, output, exist = parser()
        model = Small_llm([x.__dict__ for x in datas.funtions])
        prompts = [x.prompt for x in datas.prompts]
        refine = [
                __opten_results(i, model) for i in tqdm(prompts)
            ]
        result = [
            Output.model_validate(x).__dict__ for x in refine
            if x is not None
        ]
        if not exist and not (n := output.parent).exists():
            n.mkdir(parents=True, exist_ok=True)
        generate_output(output, result)
    except ValidationError as e:
        msgs = [err["msg"] for err in e.errors()]
        print(f"Error: {'; '.join(msgs)}", file=sys.stderr)
        return 1
    # except Exception as e:
    #     print(f"Error: {e}", file=sys.stderr)
    #     return 1
    return 0


def generate_output(file: Path, output: list[dict[str, Any]]) -> None:
    with file.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)


def __opten_results(i: str, model: Small_llm) -> Any:
    return __string_to_json(__opten_result(i, model))


def __string_to_json(str: str | None) -> Any:
    if str is None:
        return None
    try:
        return json.loads(str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}\n{str}")


def __opten_result(prompt: str, model: Small_llm) -> str | None:
    try:
        return model.communication(prompt)
    except Exception as e:
        print(f"{e}")
    return None


if __name__ == "__main__":
    sys.exit(main())
