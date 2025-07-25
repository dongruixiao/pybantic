import importlib
import inspect
from collections import defaultdict
import os
from typing import Callable, cast, overload

from pydantic import BaseModel
from pybantic.message import message, T as MessageT
from pybantic.service import (
    service,
    expose,
    T as ServiceT,
    ModelRequest as ModelRequestT,
    ModelResponse as ModelResponseT,
)
from pybantic.enums import enum, T as EnumT
from pybantic._templates import (
    MessageTemplate,
    ServiceTemplate,
    PackageTemplate,
)
from pybantic.render import (
    enums_render,
    messages_render,
    services_render,
    package_render,
)

from grpc_tools.command import build_package_protos


class Pybantic:
    def __init__(self) -> None:
        self.registry: dict[str, dict[str, list]] = defaultdict(
            lambda: defaultdict(list)
        )

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
