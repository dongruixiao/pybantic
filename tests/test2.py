from pybantic.main import Pybantic
from pydantic import BaseModel

pb = Pybantic()


@pb.message
class HelloRequest(BaseModel):
    name: str


@pb.message
class HelloResponse(BaseModel):
    message: str


@pb.service
class HelloService:
    @pb.expose
    def hello(self, request: HelloRequest) -> HelloResponse:
        return HelloResponse(message=f"Hello, {request.name}!")


if __name__ == "__main__":

    request = HelloRequest(name="World")
    service = HelloService()
    print(service.hello(request=request))  # type: ignore
