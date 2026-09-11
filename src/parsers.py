from pathlib import Path
import json
from pydantic import BaseModel, model_validator
from typing import Any


class Funtion_defined(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    returns: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def validation(self, values: dict[str, Any]) -> dict[str, Any]:
        errors = []
        lis = ["name", "description", "parameters", "returns"]
        types = ["string", "number"]
        for key, value in values.items():
            if key not in lis:
                raise ValueError("bad sintaxis in \"functions_definition\","
                                 f" they need these 4: {lis}")
            if key == "parameters":
                if not isinstance(value, dict):
                    errors.append("the parameters have been a dict")
                for _, param_v in value.items():
                    if not isinstance(param_v, dict):
                        errors.append("the parameters have"
                                      " been a dict of dict")
                        break
                    else:
                        for data_k, data_v in param_v.items():
                            self.__verif_parameters(errors, types, data_k,
                                                    data_v)
            if key == "returns":
                if not isinstance(value, dict):
                    errors.append("the return have been a dict")
                else:
                    for data_k, data_v in value.items():
                        self.__verif_parameters(errors, types, data_k, data_v)
        if errors:
            raise ValueError("\n".join(errors))
        return values

    @classmethod
    def __verif_parameters(self, errors: list[str],
                           types: list[str],
                           data_k: str, data_v: Any) -> None:
        if not isinstance(data_k, str) or data_k != "type":
            errors.append("Datas need a type of data")
        if (not isinstance(data_v, str) or
           data_v not in types):
            errors.append(f"{data_v} is not tipe of data: {types}")


class PromptInput(BaseModel):
    prompt: str

    @model_validator(mode="before")
    @classmethod
    def validation(self, values: dict[str, Any]) -> dict[str, Any]:
        lis = ["prompt"]
        for key, _ in values.items():
            if key not in lis:
                raise ValueError("bad sintaxis in \"function_calling\","
                                 f"they need these 1: {lis}")
        return values


class PromptOutput(BaseModel):
    prompt: str
    name: str
    parameters: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def validation(self, values: dict[str, Any]) -> dict[str, Any]:
        errors = []
        lis = ["prompt", "name", "parameters"]
        for key, value in values.items():
            if key not in lis:
                raise ValueError("bad sintaxis in \"function_calling_results\""
                                 f", they need these 3: {lis}")
            if key in lis[:-1]:
                if not isinstance(value, str):
                    errors.append(f"{key} is not a string")
            else:
                if not isinstance(value, dict):
                    errors.append("the parameters are a dictionary")
                else:
                    for param_k, _ in value.items():
                        if not isinstance(param_k, str):
                            errors.append("the parameters need a name")
        if errors:
            raise ValueError("\n".join(errors))
        return values


class PathConfig(BaseModel):
    functions_definition: list[Funtion_defined]
    input: list[PromptInput]
    output: list[PromptOutput]

    @model_validator(mode="before")
    @classmethod
    def validate_paths(self, values: dict[str, Path]) -> dict[str, Any]:
        errors = []
        for key, path in values.items():
            if key not in ["functions_definition", "input", "output"]:
                raise ValueError("only need 3 Paths: \functions_definition,"
                                 " input and output")
            if not path.suffix == ".json":
                errors.append(f"{key} path must be a .json file: {path}")
            if not isinstance(path, Path):
                errors.append(f"{key} must be a Path object.")
            if not path.exists() and key != "output":
                errors.append(f"{key} path does not exist: {path}")
            elif path.exists() and key != "output":
                if not path.is_file():
                    errors.append(f"{key} path is not a file: {path}")
        if errors:
            raise ValueError("\n".join(errors))
        copies = {x: y for x, y in values.items()}
        datas = {}
        for key, value in copies.items():
            if key == "functions_definition":
                datas.update(self.__get_datas(key, value, Funtion_defined))
            if key == "input":
                datas.update(self.__get_datas(key, value, PromptInput))
            if key == "output":
                datas.update(self.__get_datas(key, value, PromptOutput))
        return datas

    @classmethod
    def __get_datas(self, key: str, value: Any,
                    clas: type[BaseModel]) -> dict[str, list[Any]]:
        if isinstance(value, Path):
            datas = []
            try:
                datas = json.loads(value.read_text(encoding="utf-8"))
            except Exception:
                pass
            return {key: [clas(**x) for x in datas]}
        return {key: [clas(**x) for x in value]}

    def generate_output(self, file: Path) -> None:
        lis = [out.model_dump() for out in self.output]
        with file.open("w", encoding="utf-8") as f:
            json.dump(lis, f, indent=4)

    def verif_output(self, values: list[dict[str, Any]]) -> None:
        self.output = self.__get_datas("out", values, PromptOutput)["out"]
        if len(self.output) != len(self.input):
            raise ValueError("There aren't all anwers")


def parser_jsons(
        functions_definition: Path,
        inputs: Path,
        output: Path
        ) -> tuple[PathConfig, bool]:
    path_config = PathConfig.model_validate(
        {"functions_definition": functions_definition,
         "input": inputs,
         "output": output}
    )
    return path_config, output.exists()
