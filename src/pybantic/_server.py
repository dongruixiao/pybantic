import grpc
from concurrent import futures
import importlib
from pybantic._elements import Service


class gRPCServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    def register(self, service: Service):
        # print(importlib.import_module(service))
        pass

    def run(self):
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        self.server.start()
        self.server.wait_for_termination()
