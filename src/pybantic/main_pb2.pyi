from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

DESCRIPTOR: _descriptor.FileDescriptor

class B(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENUM_UNSPECIFIED: _ClassVar[B]
    TYPE_1: _ClassVar[B]
    TYPE_2: _ClassVar[B]

ENUM_UNSPECIFIED: B
TYPE_1: B
TYPE_2: B

class ARequest(_message.Message):
    __slots__ = ("name", "age", "height")
    NAME_FIELD_NUMBER: _ClassVar[int]
    AGE_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    name: str
    age: int
    height: float
    def __init__(
        self,
        name: _Optional[str] = ...,
        age: _Optional[int] = ...,
        height: _Optional[float] = ...,
    ) -> None: ...

class AResponse(_message.Message):
    __slots__ = (
        "message",
        "a",
        "b",
        "c",
        "d_string",
        "d_string_optional",
        "e",
        "f",
        "g",
        "h_B",
        "h_ARequest",
        "h_int32",
        "h_string",
    )
    class FEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    class GEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ARequest
        def __init__(
            self,
            key: _Optional[str] = ...,
            value: _Optional[_Union[ARequest, _Mapping]] = ...,
        ) -> None: ...

    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    A_FIELD_NUMBER: _ClassVar[int]
    B_FIELD_NUMBER: _ClassVar[int]
    C_FIELD_NUMBER: _ClassVar[int]
    D_STRING_FIELD_NUMBER: _ClassVar[int]
    D_STRING_OPTIONAL_FIELD_NUMBER: _ClassVar[int]
    E_FIELD_NUMBER: _ClassVar[int]
    F_FIELD_NUMBER: _ClassVar[int]
    G_FIELD_NUMBER: _ClassVar[int]
    H_B_FIELD_NUMBER: _ClassVar[int]
    H_AREQUEST_FIELD_NUMBER: _ClassVar[int]
    H_INT32_FIELD_NUMBER: _ClassVar[int]
    H_STRING_FIELD_NUMBER: _ClassVar[int]
    message: str
    a: ARequest
    b: B
    c: _containers.RepeatedScalarFieldContainer[str]
    d_string: str
    d_string_optional: str
    e: _containers.RepeatedCompositeFieldContainer[ARequest]
    f: _containers.ScalarMap[str, str]
    g: _containers.MessageMap[str, ARequest]
    h_B: B
    h_ARequest: ARequest
    h_int32: int
    h_string: str
    def __init__(
        self,
        message: _Optional[str] = ...,
        a: _Optional[_Union[ARequest, _Mapping]] = ...,
        b: _Optional[_Union[B, str]] = ...,
        c: _Optional[_Iterable[str]] = ...,
        d_string: _Optional[str] = ...,
        d_string_optional: _Optional[str] = ...,
        e: _Optional[_Iterable[_Union[ARequest, _Mapping]]] = ...,
        f: _Optional[_Mapping[str, str]] = ...,
        g: _Optional[_Mapping[str, ARequest]] = ...,
        h_B: _Optional[_Union[B, str]] = ...,
        h_ARequest: _Optional[_Union[ARequest, _Mapping]] = ...,
        h_int32: _Optional[int] = ...,
        h_string: _Optional[str] = ...,
    ) -> None: ...
