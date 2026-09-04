from pathlib import Path
from pydantic import BaseModel, model_validator
from typing import Any


class PathConfig(BaseModel):
    functions_definition: Path
    input: Path
    output: Path

    @model_validator(mode="before")
    @classmethod
    def validate_paths(cls, values: dict[str, Any]) -> dict[str, Path]:
        errors = []
        for key, path in values.items():
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
        return values
