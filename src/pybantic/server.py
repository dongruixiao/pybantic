import importlib
import grpc
from concurrent import futures

import inspect

from pybantic.convert import convert_from_protobuf, convert_to_protobuf


class gRPCServer:
    def __init__(self):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    @staticmethod
    def _expose_as_rpc_interface(method):
        def decorator(self, request, _):
            pd_model = method.__original_model_type__
            request = convert_from_protobuf(pd_model=pd_model, pb_message=request)
            response = method(self, request)
            return convert_to_protobuf(response)

        return decorator

    def _construct_grpc_service(self, service):
        basecls = importlib.import_module(service.__pb2_grpc_servicer__)
        service.__bases__ = (basecls, *service.__bases__)
        for name, method in inspect.getmembers(service, inspect.isfunction):
            if not hasattr(method, "__expose_as_rpc_interface__"):
                continue
            method = self._expose_as_rpc_interface(method)
            setattr(service, name, method)
        return service

    def _compile_proto(self, service):
        pass

    def _render_proto(self, service):
        pass

    def register(self, service):
        self._render_proto(service)
        self._compile_proto(service)
        pb2_grpc_module = importlib.import_module(service.__pb2_grpc_module__)
        add_to_server = getattr(
            pb2_grpc_module, f"add_{service.__class__.__name__}Servicer_to_server"
        )
        service = self._construct_grpc_service(service)
        add_to_server(service, self.server)

    @property
    def registered_services(self):
        return self.server._state.generic_handlers

    def serve(self, port: int = 50051):
        self.server.add_insecure_port(f"[::]:{port}")
        self.server.start()
        self.server.wait_for_termination()
