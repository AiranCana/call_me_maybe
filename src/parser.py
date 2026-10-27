from typing import Literal, Any
from pydantic import BaseModel
from pathlib import Path
from argparse import Namespace, ArgumentParser
import json


class TypeSpec(BaseModel):
    """Definition of a supported JSON value type in a function schema."""

    type: Literal["string", "number", "boolean", "integer"]


class Funtions(BaseModel):
    """Represent one callable function and its declared contract.

    The model uses this schema to constrain both the accepted arguments and
    the value returned by the function.
    """

    name: str
    description: str
    parameters: dict[str, TypeSpec]
    returns: TypeSpec


class Output(BaseModel):
    """Structured output emitted for a single model-generated function call."""

    prompt: str
    name: str
    parameters: dict[str, Any]


class Prompts(BaseModel):
    """Single prompt item loaded from the input evaluation dataset."""

    prompt: str


class Jsons(BaseModel):
    """Container for all parsed function definitions and prompt examples."""

    funtions: list[Funtions]
    prompts: list[Prompts]


def __parse_args() -> Namespace:
    """Parse CLI arguments for the function-calling workflow.

    Returns:
        argparse.Namespace: Parsed settings for model, IO paths,
            and visual progress output.
    """

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
    parser.add_argument(
        "--model_name",
        type=str,
        default="Qwen/Qwen3-0.6B",
    )
    parser.add_argument(
        "--visual_progress",
        action="store_true",
        default=False
    )
    return parser.parse_args()


def __read_json(jsons: Path) -> Any:
    """Read a JSON file and return its decoded Python object.

    Args:
        jsons: Path to the JSON file to load.

    Returns:
        Any: The decoded JSON payload.

    Raises:
        ValueError: If the file content cannot be parsed as JSON.
    """

    try:
        return json.loads(jsons.read_text(encoding="utf-8"))
    except Exception:
        raise ValueError("json invalid")


def __verif_json(jsons: Path, exist: bool = True) -> bool:
    """Validate that a path points to a usable JSON file.

    Args:
        jsons: File path under inspection.
        exist: Whether the file must already exist.

    Returns:
        bool: True when the path is a valid JSON file, otherwise False.
    """

    if not jsons.suffix == ".json":
        return False
    if not jsons.exists() and exist:
        return False
    if exist and not jsons.is_file():
        return False
    return True


def parser() -> tuple[Jsons, Path, bool, str, bool]:
    """Load model configuration and validate all input/output paths.

    Returns:
        tuple[Jsons, Path, bool, str, bool]: Parsed definitions, output path,
            whether it already exists, model name, and whether visual progress
            is enabled.
    """

    args = __parse_args()
    funts = Path(args.functions_definition)
    inputs = Path(args.input)
    output = Path(args.output)
    result: list[tuple[Path, bool]] = [(funts, True), (inputs, True),
                                       (output, False)]
    for i in result:
        if not __verif_json(i[0], i[1]):
            raise ValueError(f"Bad Input in {i[0]}")
    dic = {"funtions": __read_json(funts), "prompts": __read_json(inputs)}
    return (Jsons.model_validate(dic), output,
            output.exists(),
            args.model_name,
            args.visual_progress)
