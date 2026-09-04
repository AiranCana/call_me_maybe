import argparse
import sys
from pathlib import Path
from typing import Any
from src.parser import PathConfig, parser_jsons, parse_json_output
import json


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
        print("Arguments: "
              f"{path_config.functions_definition}, "
              f"{path_config.input}, "
              f"{path_config.output}")
        result = [
            __opten_result(path_config, i) for i in range(
                len(__path_to_json(path_config.input)))
            ]
        if not output_exists and not (n := path_config.output.parent).exists():
            n.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    if write_json(path_config, result) == 1:
        return 1
    return verif_output(path_config)


def verif_output(path_config: PathConfig) -> int:
    try:
        parse_json_output(path_config.output)
    except Exception as e:
        print(f"Error: the output file is invalid: {e}", file=sys.stderr)
        return 1
    return 0


def write_json(path_config: PathConfig, result: list[dict[str, Any]]) -> int:
    try:
        with path_config.output.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
    except OSError as e:
        print(f"Error: failed to write output file: {e}", file=sys.stderr)
        return 1
    return 0


def __opten_result(path_config: PathConfig, i: int) -> dict[str, Any]:
    return __string_to_json(
        pruves(
            __opten_string(path_config.functions_definition),
            __path_to_json(path_config.input)[i]["prompt"]
        )
    )


def __opten_string(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def __string_to_json(str: str) -> dict[str, Any]:
    try:
        return json.loads(str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")


def __path_to_json(path: Path) -> dict[str, Any]:
    try:
        print(__opten_string(path))
        return json.loads(__opten_string(path))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def pruves(__: dict[str, Any], _: str) -> str:
    return "The output is valid."


if __name__ == "__main__":
    sys.exit(main())
