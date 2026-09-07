import argparse
import sys
from pathlib import Path
from typing import Any
from src.parser import PathConfig, parser_jsons, parse_json_output
import json
from src import communication


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
        refine = [
            __opten_result(path_config, i) for i in range(
                len(__path_to_json(path_config.input)))
            ]
        result = [x for x in refine if x is not None]
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


def write_json(path_config: PathConfig, result: list[Any]) -> int:
    try:
        with path_config.output.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
    except OSError as e:
        print(f"Error: failed to write output file: {e}", file=sys.stderr)
        return 1
    return 0


def __opten_result(path_config: PathConfig, i: int) -> Any:
    return __string_to_json(
        pruves(
            __opten_string(path_config.functions_definition),
            __path_to_json(path_config.input)[i]["prompt"]
        )
    )


def __opten_string(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def __string_to_json(str: str | None) -> Any:
    if str is None:
        return None
    try:
        return json.loads(str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")


def __path_to_json(path: Path) -> Any:
    try:
        return json.loads(__opten_string(path))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")


def pruves(dic: str, pront: Any) -> str | None:
    try:
        final_pront = dic + pront
        communication(final_pront)
        return '{"status": "ok"}'
    except Exception as e:
        print(f"{e}")
    return None


if __name__ == "__main__":
    sys.exit(main())
