import argparse
import sys
from pathlib import Path
from src.parser_json import parser_jsons


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
    # try:
    path_config, output_exists = parser_jsons(
        functions_definition=Path(args.functions_definition),
        inputs=Path(args.input),
        output=Path(args.output)
    )
    print("Arguments: "
          f"{path_config.functions_definition}, "
          f"{path_config.input}, "
          f"{path_config.output}")
    # except Exception as e:
    #     print(f"Error: {e}", file=sys.stderr)
    #     return 1
    # return 0


if __name__ == "__main__":
    sys.exit(main())
