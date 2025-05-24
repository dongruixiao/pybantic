import typing
from pybantic._elements import Message, Service, Enum
from pybantic._types import double, int32, string


class ARequest(Message):
    name: string
    age: int32
    height: double


class B(Enum):
    TYPE_1 = 1
    TYPE_2 = 2


class AResponse(Message):
    message: str
    a: ARequest
    b: B
    c: typing.List[str]
    d: typing.Optional[str]
    e: typing.List[ARequest]
    f: typing.Dict[str, str]
    g: typing.Dict[str, ARequest]
    h: typing.Union[B, ARequest, int, str]


class A(Service):
    def hello(self, request: ARequest) -> AResponse:
        return AResponse(message=f"Hello, {request.name}!")
