from concurrent import futures
import importlib
import inspect
from collections import defaultdict
import os
from typing import Callable, overload

import grpc
from pybantic.message import message, T as MessageT
from pybantic.service import (
    service,
    expose,
    T as ServiceT,
    ModelRequest as ModelRequestT,
    ModelResponse as ModelResponseT,
)
from pybantic.enums import enum, T as EnumT

# Templates are imported in render module
from pybantic.render import (
    enums_render,
    messages_render,
    services_render,
    package_render,
)
from pybantic.convert import convert_from_protobuf, convert_to_protobuf

from grpc_tools.command import build_package_protos


class Pybantic:
    def __init__(self) -> None:
        self.registry: dict[str, dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    @overload
    def enum(
        self,
        ecls: type[EnumT],
    ) -> type[EnumT]: ...

    @overload
    def enum(
        self,
        ecls: None = None,
        /,
        *args,
        **kwargs,
    ) -> Callable[[type[EnumT]], type[EnumT]]: ...

    def enum(
        self,
        ecls: type[EnumT] | None = None,
        *args,
        **kwargs,
    ) -> type[EnumT] | Callable[[type[EnumT]], type[EnumT]]:
        return enum(
            ecls,
            pb=self,
            *args,
            **kwargs,
        )

    @overload
    def message(
        self,
        mcls: type[MessageT],
    ) -> type[MessageT]: ...

    @overload
    def message(
        self,
        mcls: None = None,
        /,
        *args,
        **kwargs,
    ) -> Callable[[type[MessageT]], type[MessageT]]: ...

    def message(
        self,
        mcls: type[MessageT] | None = None,
        *args,
        **kwargs,
    ) -> type[MessageT] | Callable[[type[MessageT]], type[MessageT]]:
        return message(
            mcls,
            pb=self,
            *args,
            **kwargs,
        )

    @overload
    def service(
        self,
        scls: type[ServiceT],
    ) -> type[ServiceT]: ...

    @overload
    def service(
        self,
        scls: None = None,
        /,
        *args,
        **kwargs,
    ) -> Callable[[type[ServiceT]], type[ServiceT]]: ...

    def service(
        self,
        scls: type[ServiceT] | None = None,
        *args,
        **kwargs,
    ) -> type[ServiceT] | Callable[[type[ServiceT]], type[ServiceT]]:
        return service(
            scls,
            pb=self,
            *args,
            **kwargs,
        )

    def expose(
        self,
        smtd: Callable[
            [ServiceT, ModelRequestT],
            ModelResponseT,
        ],
    ) -> Callable[
        [ServiceT, ModelRequestT],
        ModelResponseT,
    ]:
        return expose(method=smtd)

    def register(self, element: type[MessageT | ServiceT]) -> None:
        element_type = element.__pybantic_type__  # type: ignore
        absfile = inspect.getabsfile(element)
        self.registry[absfile][element_type].append(element)

    def generate(self) -> None:
        for file_path, elements in self.registry.items():
            element_list = []
            for element_type, elements in elements.items():
                if element_type == "message":
                    element_list += messages_render(elements)
                elif element_type == "service":
                    element_list += services_render(elements)
                elif element_type == "enum":
                    element_list += enums_render(elements)
                else:
                    raise ValueError(f"Unsupported element type: {element_type}")

            package_name = os.path.basename(file_path).replace(".py", "")
            package = package_render(package_name, element_list)
            target_path = file_path.replace(".py", ".proto")
            with open(target_path, "w") as f:
                f.write(package)

    def compile(self) -> None:
        for file_path, elements in self.registry.items():
            target_dir = os.path.dirname(file_path)
            build_package_protos(package_root=target_dir)

    def _register_available_services(self):
        for file_path, elements in self.registry.items():
            for element_type, elements in elements.items():
                if element_type == "service":
                    for element in elements:
                        source_file = inspect.getfile(element)
                        filename = os.path.splitext(os.path.basename(source_file))[0]
                        pb2_grpc_module_name = f"{filename}_pb2_grpc"

                        svccls = importlib.import_module(pb2_grpc_module_name)
                        basecls = getattr(svccls, f"{element.__name__}Servicer")
                        ServiceAdapter = self._create_service_adapter(element, basecls)
                        service_adapter = ServiceAdapter()

                        add_to_server = getattr(
                            svccls,
                            f"add_{element.__name__}Servicer_to_server",
                        )
                        add_to_server(service_adapter, self.server)

    def _create_service_adapter(self, element, basecls):
        """创建服务适配器，将 gRPC 调用适配到用户定义的 pydantic 方法"""

        # 获取用户服务类的实例
        user_service = element

        # 收集所有暴露的方法及其类型信息
        exposed_methods = {}
        for attr_name in dir(user_service):
            attr = getattr(user_service, attr_name)
            if (
                hasattr(attr, "__pybantic_type__")
                and attr.__pybantic_type__ == "method"
            ):
                # 获取方法的类型注解
                signature = inspect.signature(attr)
                params = list(signature.parameters.values())
                if len(params) >= 2:  # self + request
                    request_type = params[1].annotation
                    response_type = signature.return_annotation
                    exposed_methods[attr_name] = {
                        "method": attr,
                        "request_type": request_type,
                        "response_type": response_type,
                    }

        class ServiceAdapter(basecls):
            def __init__(self):
                super().__init__()

        # 动态为每个暴露的方法创建适配器
        for method_name, method_info in exposed_methods.items():

            def create_adapter_method(user_method, req_type, resp_type):
                def adapter_method(self, request, context):
                    try:
                        # 将 protobuf request 转换为 pydantic model
                        pydantic_request = convert_from_protobuf(req_type, request)

                        # 调用用户方法
                        pydantic_response = user_method(self, request=pydantic_request)

                        # 将 pydantic response 转换为 protobuf message
                        protobuf_response = convert_to_protobuf(pydantic_response)

                        return protobuf_response
                    except Exception as e:
                        context.set_code(grpc.StatusCode.INTERNAL)
                        context.set_details(f"Internal error: {str(e)}")
                        raise e

                return adapter_method

            # 将适配器方法绑定到 ServiceAdapter 类
            adapter_method = create_adapter_method(
                method_info["method"],
                method_info["request_type"],
                method_info["response_type"],
            )
            setattr(ServiceAdapter, method_name, adapter_method)

        return ServiceAdapter

    def run(self, port: int = 50051) -> None:
        self._register_available_services()
        self.server.add_insecure_port(f"[::]:{port}")
        self.server.start()
        print(f"Server started on port {port}")
        self.server.wait_for_termination()
