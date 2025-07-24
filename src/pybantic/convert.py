from typing import Any
from pydantic import BaseModel, ValidationError, create_model
from pydantic.fields import FieldInfo
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToDict


def _handle_field_missing(field_name: str, field_info: FieldInfo) -> None:
    pass


def _handle_field_in_list(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _handle_field_in_dict(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _handle_field_in_enum(field_name: str, field_info: FieldInfo, pb_value: Any) -> Any:
    pass


def _construct_model_data(
    pd_fields: dict[str, FieldInfo], pb_msg_dict: dict[str, Any]
) -> dict[str, Any]:
    data = {}
    for name, info in pd_fields.items():
        missing = name not in pb_msg_dict
        if missing:
            data[name] = _handle_field_missing(name, info)
            continue

        pb_value = pb_msg_dict[name]
        if info.annotation is not None:
            data[name] = info.annotation.from_protobuf(pb_value)
        else:
            data[name] = pb_value

    return data


def convert_from_protobuf(pd_model: type[BaseModel], pb_message: Message) -> BaseModel:
    # pb_msg_dict = MessageToDict(
    #     pb_message,
    #     preserving_proto_field_name=True,
    # )
    # pd_fields = pd_model.__pydantic_fields__
    # data = _construct_model_data(pd_fields, pb_msg_dict)
    # try:
    #     return pd_model.model_validate(data)
    # except ValidationError as e:
    #     raise ValueError(f"Failed to convert from protobuf: {e}")
    model = create_model("A", **{"name": int})
    return model.model_validate({"name": 123})


def convert_to_protobuf(pd_model: BaseModel) -> Message:
    return Message()
