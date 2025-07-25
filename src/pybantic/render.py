import inspect
import typing
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from pybantic._templates import (
    EnumItemTemplate,
    EnumTemplate,
    FieldTemplate,
    LabelFieldTemplate,
    MessageTemplate,
    MethodTemplate,
    OneOfTemplate,
    PackageTemplate,
    ServiceTemplate,
)
from pybantic.types import (
    get_scalar_type,
    is_enum_type,
    is_map_type,
    is_message_type,
    is_method_type,
    is_scalar_type,
)


def scalar_type_render(index, name, field_info, label: str | None = None) -> str:
    if not is_scalar_type(field_info.annotation):
        raise ValueError(f"Unsupported scalar type: {field_info.annotation}")

    if label:
        return LabelFieldTemplate(
            index=index,
            name=name,
            type=get_scalar_type(field_info.annotation),
            label=label,
        ).render()

    return FieldTemplate(
        index=index,
        name=name,
        type=get_scalar_type(field_info.annotation),
    ).render()


def message_type_render(index, name, field_info, label: str | None = None) -> str:
    if not is_message_type(field_info.annotation):
        raise ValueError(f"Unsupported message type: {field_info.annotation}")

    if label:
        return LabelFieldTemplate(
            index=index,
            name=name,
            type=field_info.annotation.__name__,
            label=label,
        ).render()

    return FieldTemplate(
        index=index,
        name=name,
        type=field_info.annotation.__name__,
    ).render()


def enum_type_render(index, name, field_info, label: str | None = None) -> str:
    if not is_enum_type(field_info.annotation):
        raise ValueError(f"Unsupported enum type: {field_info.annotation}")

    if label:
        return LabelFieldTemplate(
            index=index,
            name=name,
            type=field_info.annotation.__name__,
            label=label,
        ).render()

    return FieldTemplate(
        index=index,
        name=name,
        type=field_info.annotation.__name__,
    ).render()


def map_type_render(index, name, field_info) -> str:
    args = typing.get_args(field_info.annotation)
    key_type, value_type = args[0], args[1]
    if not is_map_type(key_type, value_type):
        raise ValueError(f"Unsupported map type: {key_type}, {value_type}")
    key_type_str = get_scalar_type(key_type)
    value_type_str = (
        get_scalar_type(value_type)
        if is_scalar_type(value_type)
        else value_type.__name__
    )
    type_str = f"map<{key_type_str}, {value_type_str}>"
    return FieldTemplate(
        index=index,
        name=name,
        type=type_str,
    ).render()


def none_type_render(index, name, field_info) -> str:
    return FieldTemplate(
        index=index,
        name=name,
        type="string",
    ).render()


def oneof_type_render(index, name, field_info) -> str:
    args = typing.get_args(field_info.annotation)
    oneof_fields = []
    for jndex, arg in enumerate(args, start=1):
        index = index * 10_000 + jndex
        if is_scalar_type(arg):
            oneof_field = scalar_type_render(index, name, FieldInfo(annotation=arg))
        if is_message_type(arg):
            oneof_field = message_type_render(index, name, FieldInfo(annotation=arg))
        if is_enum_type(arg):
            oneof_field = enum_type_render(index, name, FieldInfo(annotation=arg))
        if isinstance(None, arg):
            oneof_field = none_type_render(index, name, FieldInfo(annotation=arg))
        else:
            raise ValueError(f"Unsupported type: {arg}")
        oneof_fields.append(oneof_field)
    return OneOfTemplate(
        name=name,
        fields=oneof_fields,
    ).render()


def field_render(index, name, field_info: FieldInfo) -> str:
    typing_origin = typing.get_origin(field_info.annotation)
    typing_args = typing.get_args(field_info.annotation)
    if not typing_origin:
        if is_scalar_type(field_info.annotation):
            return scalar_type_render(index, name, field_info)
        if is_message_type(field_info.annotation):
            return message_type_render(index, name, field_info)
        if is_enum_type(field_info.annotation):
            return enum_type_render(index, name, field_info)
        raise ValueError(f"Unsupported origin type: {field_info.annotation}")
    if not typing_args:
        raise ValueError(
            f"Please specify the arguments of the field type: {field_info.annotation}"
        )
    if typing_origin is list:
        args0 = typing_args[0]
        if is_scalar_type(args0):
            return scalar_type_render(index, name, field_info, label="repeated")
        if is_message_type(args0):
            return message_type_render(index, name, field_info, label="repeated")
        if is_enum_type(args0):
            return enum_type_render(index, name, field_info, label="repeated")
        raise ValueError(f"Unsupported repeated type: {field_info.annotation}")
    if typing_origin is dict:
        return map_type_render(index, name, field_info)
    if typing_origin is typing.Union:
        return oneof_type_render(index, name, field_info)
    raise ValueError(f"Unsupported type: {field_info.annotation}")


def fields_render(field_infos: list[tuple[str, FieldInfo]]) -> list[str]:
    return [
        field_render(
            index=index,
            name=name,
            field_info=field_info,
        )
        for index, (name, field_info) in enumerate(
            field_infos,
            start=1,
        )
    ]


def message_render(message: BaseModel):
    field_infos = message.__pydantic_fields__.items()
    return MessageTemplate(
        name=message.__name__,
        fields=fields_render(
            field_infos=list(
                field_infos,
            )
        ),
    ).render()


def messages_render(messages: list[BaseModel]) -> list[str]:
    return [message_render(message) for message in messages]


def method_render(method):
    annotations = inspect.get_annotations(method)
    response = annotations.pop("return")
    request = annotations.popitem()[1]
    return MethodTemplate(
        name=method.__name__,
        request=request.__name__,
        response=response.__name__,
    ).render()


def methods_render(methods):
    return [method_render(method) for method in methods]


def service_render(service):
    methods = methods_render(
        [
            method
            for _, method in inspect.getmembers(service, inspect.isfunction)
            if is_method_type(method)
        ]
    )
    return ServiceTemplate(
        name=service.__name__,
        methods=methods,
    ).render()


def services_render(services):
    return [service_render(service) for service in services]


def enum_item_render(index, name):
    return EnumItemTemplate(
        name=name,
        index=index,
    ).render()


def enum_items_render(enum):
    return [
        enum_item_render(index, name)
        for index, (name, _) in enumerate(
            iterable=enum.__members__.items(),
            start=1,
        )
    ]


def enum_render(enum):
    items = enum_items_render(enum)
    return EnumTemplate(
        name=enum.__name__,
        items=items,
    ).render()


def enums_render(enums):
    return [enum_render(enum) for enum in enums]


def package_render(name, elements, imports=[]):
    return PackageTemplate(
        name=name,
        elements=elements,
        imports=imports,
    ).render()
