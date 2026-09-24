from typing import Literal, Any
from pydantic import BaseModel
from pathlib import Path
from argparse import Namespace, ArgumentParser
import json


class TypeSpec(BaseModel):
    type: Literal["string", "number", "boolean"]


class Funtions(BaseModel):
    name: str
    description: str
    parameters: dict[str, TypeSpec]
    returns: TypeSpec


class Output(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, Any]


class Prompts(BaseModel):
    prompt: str


class Jsons(BaseModel):
    funtions: list[Funtions]
    prompts: list[Prompts]


def __parse_args() -> Namespace:
    parser = ArgumentParser()
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


def __read_json(jsons: Path) -> str:
    try:
        return json.loads(jsons.read_text(encoding="utf-8"))
    except Exception:
        raise ValueError("json invalid")


def __verif_json(jsons: Path, exist: bool = True) -> bool:
    if not jsons.suffix == ".json":
        return False
    if not jsons.exists() and exist:
        return False
    if exist and not jsons.is_file():
        return False
    return True


def parser() -> tuple[Jsons, Path, bool]:
    args = __parse_args()
    funts = Path(args.functions_definition)
    inputs = Path(args.input)
    output = Path(args.output)
    for i in [[funts, True], [inputs, True], [output, False]]:
        if not __verif_json(i[0], i[1]):
            raise ValueError(f"Bad Input in {i[0]}")
    dic = {"funtions": __read_json(funts), "prompts": __read_json(inputs)}
    return Jsons.model_validate(dic), output, output.exists()
