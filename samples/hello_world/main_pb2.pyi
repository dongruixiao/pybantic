from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AEnum(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ENUM_UNSPECIFIED: _ClassVar[AEnum]
    A: _ClassVar[AEnum]
    B: _ClassVar[AEnum]
    C: _ClassVar[AEnum]
ENUM_UNSPECIFIED: AEnum
A: AEnum
B: AEnum
C: AEnum

class ARequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class AResponse(_message.Message):
    __slots__ = ("message", "enum")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ENUM_FIELD_NUMBER: _ClassVar[int]
    message: str
    enum: AEnum
    def __init__(self, message: _Optional[str] = ..., enum: _Optional[_Union[AEnum, str]] = ...) -> None: ...
