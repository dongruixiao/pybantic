from pybantic.service import service, expose
from pybantic.message import message
from pydantic import BaseModel


@message
class ARequest(BaseModel):
    name: str


@message
class AResponse(BaseModel):
    message: str


@service
class HelloService:
    @expose
    def hello(self, request: ARequest) -> AResponse:
        return AResponse(message=f"Hello, {request.name}!")




# service_instance = HelloService()
# request = ARequest(name="dongruixiao")

# print(service_instance)
