from typing import Any
from src.parser_path import PathConfig
from pathlib import Path
import json


def parse_json_functions(json_path: Path) -> list[dict[str, Any]]:
    data = vasic_parse_jsons(json_path)
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid input format in {json_path}: "
                             "Each item must be a dictionary.")
        for key in ["name", "description", "parameters", "returns"]:
            if key not in item:
                raise ValueError(f"Missing key '{key}' in input item: {item}")
            verif_name_description(item, key)
            verif_param_return(item, key)
    return data


def parse_json_input(json_path: Path) -> list[dict[str, Any]]:
    data = vasic_parse_jsons(json_path)
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Invalid input format in {json_path}: "
                             "Each item must be a dictionary.")
        if item.get("prompt") is None:
            raise ValueError(f"Missing 'prompt' key in input item: {item}")
        if not isinstance(item["prompt"], str):
            raise ValueError(f"Invalid type for 'prompt' in input item: "
                             f"{item}. Expected a string.")
    return data


def parse_json_output(json_path: Path) -> list[dict[str, Any]]:
    data = vasic_parse_jsons(json_path)
    return data


def verif_param_return(item: dict[str, Any], key: Any) -> None:
    if key == "parameters":
        if not isinstance(item[key], dict):
            raise ValueError(f"Invalid type for 'parameters' in input item:"
                             f" {item}. Expected a dictionary.")
        for param_key, param_value in item[key].items():
            validate_type(
                        item, param_value, isinstance(param_key, str))
    if key == "returns":
        if not isinstance(item[key], dict):
            raise ValueError(f"Invalid type for 'returns' in input item:"
                             f" {item}. Expected a dictionary.")
        for return_key, return_value in item[key].items():
            validate_type(
                        item, return_key, isinstance(return_key, str), False)


def verif_name_description(item: dict[str, Any], key: Any) -> None:
    if key in ["name", "description"]:
        if not isinstance(item[key], str):
            raise ValueError(
                f"Invalid type for '{key}' "
                f"in input item: {item}. Expected a string.")


def validate_type(item: dict[str, Any], param_value: Any,
                  is_param_key_not_valid: bool,
                  is_not_return: bool = True) -> None:
    if not is_param_key_not_valid:
        raise ValueError(f"Invalid parameter key type in input item: {item}. "
                         "Expected a string.")
    if is_not_return:
        if not isinstance(param_value, (dict)):
            print(f"param_value: {param_value}, type: {type(param_value)}")
            raise ValueError(f"Invalid parameter value type in input item: "
                             f"{item}. Expected a dictionary.")
        for sub_key in param_value:
            verif_type_name(item, sub_key)
    else:
        verif_type_name(item, param_value)


def verif_type_name(item, sub_key):
    if not isinstance(sub_key, str) and sub_key != "type":
        raise ValueError(f"Invalid sub-key type in input item: {item}."
                         " Expected a string.")


def vasic_parse_jsons(json_path: Path) -> Any:
    content = json_path.read_text(encoding="utf-8")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {json_path}: {e}")
    if not isinstance(data, list):
        raise ValueError(f"Invalid input format in {json_path}: "
                         "Expected a list of dictionaries.")
    return data


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
    parse_json_functions(functions_definition)
    parse_json_input(inputs)
    return path_config, output.exists()
