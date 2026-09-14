import argparse
import sys
from pathlib import Path
from pydantic import TypeAdapter, ValidationError
from typing import Any
from src.parsers import PathConfig, parser_jsons, Funtion_defined
import json
from src import Small_llm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--functions_definition",
        type=str,
        default="data/input/functions_definition.json",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/input/function_calling_tests.json",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output/function_calling_results.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        path_config, output_exists = parser_jsons(
            functions_definition=Path(args.functions_definition),
            inputs=Path(args.input),
            output=Path(args.output)
        )
        model = Small_llm()
        refine = [
            __opten_result(path_config, i, model) for i in range(
                len(path_config.input))
            ]
        result = [x for x in refine if x is not None]
        path_config.verif_output(result)
        if not output_exists and not (n := Path(args.output).parent).exists():
            n.mkdir(parents=True, exist_ok=True)
        path_config.generate_output(Path(args.output))
    except ValidationError as e:
        msgs = [err["msg"] for err in e.errors()]
        print(f"Error: {'; '.join(msgs)}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def __opten_result(path_config: PathConfig, i: int) -> Any:
    return __string_to_json(
        pruves(
            __opten_string(path_config.functions_definition),
            path_config.input[i].prompt
        )
    )


def __opten_string(output: list[Any]) -> str:
    adapter = TypeAdapter(list[Funtion_defined])
    return adapter.dump_json(output).decode("utf-8")


def __string_to_json(str: str | None) -> Any:
    if str is None:
        return None
    try:
        return json.loads(str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")


def pruves(dic: str, pront: Any, model: Small_llm) -> str | None:
    try:
        final_pront = dic + pront
        # return model.communication(final_pront)
        return '{"status": "ok"}'
    except Exception as e:
        print(f"{e}")
    return None


if __name__ == "__main__":
    sys.exit(main())
