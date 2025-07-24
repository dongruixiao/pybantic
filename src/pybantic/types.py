from typing import Any, NewType

# Type Alias
double = NewType("double", float)
int32 = NewType("int32", int)
int64 = NewType("int64", int)
uint32 = NewType("uint32", int)
uint64 = NewType("uint64", int)
sint32 = NewType("sint32", int)
sint64 = NewType("sint64", int)
fixed32 = NewType("fixed32", int)
fixed64 = NewType("fixed64", int)
sfixed32 = NewType("sfixed32", int)
sfixed64 = NewType("sfixed64", int)
string = NewType("string", str)


SCALAR_TYPE_PY_TO_PB: dict[Any, str] = {
    # built-in types
    float: "float",
    int: "int32",
    bool: "bool",
    str: "string",
    bytes: "bytes",
    # alias types
    double: "double",
    int32: "int32",
    int64: "int64",
    uint32: "uint32",
    uint64: "uint64",
    sint32: "sint32",
    sint64: "sint64",
    fixed32: "fixed32",
    fixed64: "fixed64",
    sfixed32: "sfixed32",
    sfixed64: "sfixed64",
    string: "string",
}

SCALAR_TYPE_PB_TO_PY: dict[str, Any] = {
    "double": float,
    "float": float,
    "int32": int,
    "int64": int,
    "uint32": int,
    "uint64": int,
    "sint32": int,
    "sint64": int,
    "fixed32": int,
    "fixed64": int,
    "sfixed32": int,
    "sfixed64": int,
    "bool": bool,
    "string": str,
    "bytes": bytes,
}


def get_scalar_type(type: Any) -> str:
    return SCALAR_TYPE_PY_TO_PB[type]


def is_scalar_type(type: Any) -> bool:
    return type in SCALAR_TYPE_PY_TO_PB


def is_map_key_type(type: Any) -> bool:
    return type in SCALAR_TYPE_PY_TO_PB and type not in [
        float,
        double,
        bytes,
    ]


def is_map_value_type(type: Any) -> bool:
    if is_scalar_type(type):
        return True
    if is_message_type(type):
        return True
    if is_enum_type(type):
        return True
    return False


def is_map_type(key_type: Any, value_type: Any) -> bool:
    # where the key_type can be any integral or string type
    #  (so, any scalar type except for floating point types and bytes).
    #  Note that neither enum nor proto messages are valid for key_type.
    # The value_type can be any type except another map.
    return is_map_key_type(key_type) and is_map_value_type(value_type)


def is_message_type(type: Any) -> bool:
    return getattr(type, "__pybantic_message__", False)


def is_enum_type(type: Any) -> bool:
    return getattr(type, "__pybantic_enum__", False)


def is_service_type(type: Any) -> bool:
    return getattr(type, "__pybantic_service__", False)
