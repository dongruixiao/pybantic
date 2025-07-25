import enum
from pydantic import BaseModel

from pybantic.main import Pybantic

pb = Pybantic()


@pb.message
class ARequest(BaseModel):
    name: str


@pb.enum
class AEnum(enum.IntEnum):
    A = 1
    B = 2
    C = 3


@pb.message
class AResponse(BaseModel):
    message: str
    enum: AEnum


@pb.service
class HelloService:
    @pb.expose
    def hello(self, request: ARequest) -> AResponse:
        return AResponse(message=f"Hello, {request.name}!")


pb.generate()
pb.compile()
