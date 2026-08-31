from pathlib import Path
from pydantic import BaseModel, model_validator


class PathConfig(BaseModel):
    functions_definition: Path
    input: Path
    output: Path

    @model_validator(mode="before")
    @classmethod
    def validate_paths(cls, values: dict[str, Path]) -> dict[str, Path]:
        for key, path in values.items():
            if not isinstance(path, Path):
                raise ValueError(f"{key} must be a Path object.")
            if not path.exists() and key != "output":
                raise ValueError(f"{key} path does not exist: {path}")
            elif path.exists():
                if not path.is_file():
                    raise ValueError(f"{key} path is not a file: {path}")
            if not path.suffix == ".json":
                raise ValueError(
                    f"{key} path must be a .json file: {path}")
        return values
