from pybantic.client import create_client
from main import HelloService, ARequest

client = create_client(service_class=HelloService, target="localhost:50051")

response = client.hello(request=ARequest(name="World"))
print(response)
