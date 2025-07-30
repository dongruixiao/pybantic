import importlib
import inspect
import os
from typing import Any
from pydantic import BaseModel, ValidationError, create_model
from pydantic.fields import FieldInfo
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToDict
import typing
from google.protobuf import json_format

from pybantic.types import is_enum_type, is_map_type, is_message_type


def _handle_field_missing(field_name: str, field_info: FieldInfo) -> None:
    pass


def _handle_field_in_list(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _handle_field_in_dict(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _handle_field_in_enum(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _construct_model_data(
    model_fields: dict[str, FieldInfo], message_dict: dict[str, Any]
) -> dict[str, Any]:
    data = {}
    for name, info in model_fields.items():
        if name not in message_dict:
            data[name] = _handle_field_missing(name, info)
            continue

        value = message_dict[name]
        if not info.annotation:
            raise ValueError(f"Field {name} has no annotation")

        origin = typing.get_origin(info.annotation)
        if not origin:
            if is_message_type(info.annotation):
                data[name] = convert_from_protobuf(info.annotation, value)
            elif is_enum_type(info.annotation):
                data[name] = info.annotation[value]  # type:ignore
            else:
                data[name] = value
        elif origin is typing.Literal:
            if value in typing.get_args(info.annotation):
                data[name] = value
        elif origin is list:
            args0 = typing.get_args(info.annotation)[0]
            if is_message_type(args0):
                data[name] = [convert_from_protobuf(args0, item) for item in value]
            elif is_enum_type(args0):
                data[name] = [args0[item] for item in value]
            else:
                data[name] = list(value)
        elif origin is dict:
            args0, args1 = typing.get_args(info.annotation)
            assert is_map_type(args0, args1)
            data[name] = dict(value)
        elif origin is typing.Union:
            if value is None:
                data[name] = None
                continue
            possible_types = [
                t for t in typing.get_args(info.annotation) if t is not type(None)
            ]
            actual_type = type(value)
            matched_type = None
            for possible_type in possible_types:
                if actual_type == possible_type:
                    matched_type = possible_type
                    break
            if not matched_type:
                for possible_type in possible_types:
                    if isinstance(value, possible_type):
                        matched_type = possible_type
                        break
            if not matched_type:
                raise ValueError(f"Failed to convert from protobuf: {value}")
            if is_message_type(matched_type):
                data[name] = convert_from_protobuf(matched_type, value)
            elif is_enum_type(matched_type):
                data[name] = matched_type[value]
            else:
                data[name] = value
        else:
            raise ValueError(f"Unsupported field type: {origin}")
    return data


def convert_from_protobuf(
    model: type[BaseModel], message: Message | dict[str, Any]
) -> BaseModel:
    if isinstance(message, Message):
        message = MessageToDict(
            message=message,
            preserving_proto_field_name=True,
        )
    model_fields = model.__pydantic_fields__
    data = _construct_model_data(model_fields, message)
    try:
        return model.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Failed to convert from protobuf: {e}")


def convert_to_protobuf(model: BaseModel) -> Message:
    source_file = inspect.getfile(model.__class__)
    filename = os.path.splitext(os.path.basename(source_file))[0]
    pb2_module_name = f"{filename}_pb2"

    mgscls = importlib.import_module(pb2_module_name)
    message_class = getattr(mgscls, model.__class__.__name__)
    message = message_class()
    # msgcls = "" if model.__module__ == "__main__" else model.__module__
    # msgcls += "." if msgcls else ""
    # msgcls += model.__class__.__name__
    # msgcls += "_pb2"
    # mgscls = importlib.import_module(msgcls)
    # message = mgscls()  # type:ignore
    return json_format.ParseDict(model.model_dump(), message)
