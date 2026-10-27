import sys
from pathlib import Path
from pydantic import ValidationError
from typing import Any
import json
import re
from tqdm import tqdm
from src import Small_llm
from src.parser import parser, Output


def main() -> int:
    """Run the end-to-end function-calling workflow.

    Returns:
        int: Exit code for the CLI run. Zero on success; one on validation or
            runtime failure.
    """

    try:
        datas, output, exist, model_name, visual = parser()
        model = Small_llm([x.__dict__ for x in datas.funtions],
                          model_name,
                          visual)
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
        tqdm.write(f"Error: {'; '.join(msgs)}", file=sys.stderr)
        return 1
    except Exception as e:
        tqdm.write(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def generate_output(file: Path, output: list[dict[str, Any]]) -> None:
    """Write the final JSON output to a file in a readable format.

    Args:
        file: Destination file path.
        output: List of validated result dictionaries to store.
    """

    with file.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)


def __opten_results(i: str, model: Small_llm) -> Any:
    """Process a single prompt and normalize the returned JSON payload.

    Args:
        i: User prompt to evaluate.
        model: Model instance used to generate the result.

    Returns:
        Any: Parsed output object or None if processing fails.
    """

    try:
        return __string_to_json(__opten_result(i, model))
    except Exception as e:
        tqdm.write(f"Error processing prompt '{i}': {e}", file=sys.stderr)
        return None


def __string_to_json(str: str | None) -> Any:
    """Convert a JSON string into Python objects with a fallback escape repair.

    Args:
        str: Serialized JSON text.

    Returns:
        Any: Decoded JSON object, or None if no value was provided.

    Raises:
        ValueError: If the string still cannot be parsed as valid JSON.
    """

    if str is None:
        return None
    try:
        return json.loads(str)
    except json.JSONDecodeError:
        str = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', str)
        try:
            return json.loads(str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string: {e}\n"
                             f"the json is: {str}")


def __opten_result(prompt: str, model: Small_llm) -> str | None:
    """Generate a raw completion for a prompt and return it if successful.

    Args:
        prompt: User prompt to generate a response for.
        model: Model instance responsible for inference.

    Returns:
        str | None: Raw model response string, or None if generation fails.
    """

    try:
        return model.communication(prompt)
    except Exception as e:
        tqdm.write(f"Error processing prompt '{prompt}': {e}", file=sys.stderr)
    return None


if __name__ == "__main__":
    sys.exit(main())
