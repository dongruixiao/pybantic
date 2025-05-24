from typing import NewType, Optional

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


_scalar_type_py_to_pb = {
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

_optional_type_py_to_pb = {
    Optional[int]: "int32",
    Optional[float]: "float",
    Optional[bool]: "bool",
    Optional[str]: "string",
    Optional[bytes]: "bytes",
}

_scalar_type_pb_to_py = {
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


# DEAFULT_VALUE = {
#     float: 0,
#     int: 0,
#     bool: False,
#     str: "",
#     bytes: b"",
#     list: [],
#     dict: {},
#     # message {}??
#     # enum 0
# }


# 别名，默认值
# option allow_alias = true;

# enum Corpus {
#   CORPUS_UNSPECIFIED = 0; // 默认值
#   CORPUS_UNIVERSAL = 1;
#   CORPUS_WEB = 2;
#   CORPUS_IMAGES = 3;
#   CORPUS_LOCAL = 4;
#   CORPUS_NEWS = 5;
#   CORPUS_PRODUCTS = 6;
#   CORPUS_VIDEO = 7;
# }


def transfer_py_to_pb_type(py_type, default_value=None):
    if py_type in _scalar_type_py_to_pb:
        return _scalar_type_py_to_pb[py_type]

    # Optional 的常规类型，如 int, float, bool, str, bytes
    #      默认值为 None 或者默认值为 0， “”，b""，0.0，False
    # Optional 的特殊类型，如 list, dict, Enum，自定义类，自定义的 Pydantic 类型
    # List 类型
    # Map 类型
    # Enum 类型
    # 自定义类
    # 自定义的 Pydantic 类型

    if py_type in _optional_type_py_to_pb:
        py_type = _optional_type_py_to_pb[py_type]


def transfer_pb_to_py_type(pb_type: str):
    # pb 支持的类型
    # 标量类型
    # enum 类型
    # Messagex 类型
    # ANY 类型
    # ONE OF
    # optional 类型
    # repeated 类型
    # map 类型
    # 自定义类
    # 自定义的 Pydantic 类型

    if pb_type in _scalar_type_pb_to_py:
        return _scalar_type_pb_to_py[pb_type]


if __name__ == "__main__":
    from pydantic import BaseModel, Field
    from typing import Annotated

    class Test(BaseModel):
        a: Annotated[int | None, "hahah"] = 1

    print(Test.__pydantic_fields__["a"].annotation)
    print(Test.__pydantic_fields__["a"].metadata)
