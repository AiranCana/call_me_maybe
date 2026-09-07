from pathlib import Path
from src.parser.parser_json import (parse_json_functions,
                                    parse_json_input)
import json
from pydantic import BaseModel, model_validator
from typing import Any


class Funtion_defined(BaseModel):
    name: str
    descripcion: str
    parameters: dict[str, Any]
    returns: dict[str, Any]


class PromptInput(BaseModel):
    prompt: str


class PathConfig(BaseModel):
    functions_definition: Path
    input: Path
    output: Path

    @model_validator(mode="before")
    @classmethod
    def validate_paths(cls, values: dict[str, Any]) -> dict[str, Path]:
        errors = []
        for key, path in values.items():
            if key not in ["functions_definition", "input", "output"]:
                raise ValueError("only need 3 Paths: functions_definition, input and output")
            if not path.suffix == ".json":
                errors.append(f"{key} path must be a .json file: {path}")
            if not isinstance(path, Path):
                errors.append(f"{key} must be a Path object.")
            if not path.exists() and key != "output":
                errors.append(f"{key} path does not exist: {path}")
            elif path.exists():
                if not path.is_file():
                    errors.append(f"{key} path is not a file: {path}")
        if errors:
            raise ValueError("\n".join(errors))
        copies = {x: y for x, y in values.items()}
        datas = {}
        for key, value in copies.items():
            if key == "functions_definition":
                datas.update(key: [Funtion_defined(x) for x in list(json.loads(value.read_text(encoding="utf-8")))])

        return values

    @model_validator(mode="after")
    def verif_json(self) -> "PathConfig":
        parse_json_functions(self.functions_definition)
        parse_json_input(self.input)
        return self


def parser_jsons(
        functions_definition: Path,
        inputs: Path,
        output: Path
        ) -> tuple[PathConfig, bool]:
    path_config = PathConfig(
        functions_definition=functions_definition,
        input=inputs,
        output=output
    )
    return path_config, output.exists()
