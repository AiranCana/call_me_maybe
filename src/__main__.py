import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--functions_definition",
                        type=str,
                        default="data/input/functions_definition.json",)
    parser.add_argument("--input", help="Input file")
    
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        print(f"Arguments: {args}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0
