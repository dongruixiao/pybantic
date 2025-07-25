import importlib
import os
import typing
import enum
import inspect
from collections import defaultdict
from grpc_tools.command import build_package_protos
from pydantic import BaseModel
from typing import get_args, get_origin
from functools import wraps

from pybantic._templates import (
    EnumItemTemplate,
    EnumTemplate,
    FieldTemplate,
    LabelFieldTemplate,
    MessageTemplate,
    MethodTemplate,
    OneOfTemplate,
    ServiceTemplate,
    PackageTemplate,
)

from pybantic._types import _scalar_type_py_to_pb
from google.protobuf import json_format

T = typing.TypeVar("T", bound="_ElementRegistry")


class ElementType(enum.StrEnum):
    Message: str = "Message"
    Service: str = "Service"
    Enum: str = "Enum"


class _ElementRegistry:
    __registered_elements: typing.ClassVar[dict[str, dict[ElementType, list[T]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    __register_strategy: typing.ClassVar[typing.Literal["user", "all"]] = (  # TODO:
        "user"
    )

    def __init_subclass__(cls, register_strategy: str = "all", **kwargs):
        cls.__register_strategy = register_strategy
        if _ElementRegistry in cls.__bases__ or any(
            [issubclass(basecls, _ElementRegistry) for basecls in cls.__bases__]
        ):
            clsmodule = cls.__module__
            clsname = cls.__name__
            if cls.__register_strategy == "user" and not cls.__is_user_defined(
                clsmodule
            ):
                super().__init_subclass__(**kwargs)
                return
            if clsname not in ElementType.__members__ and clsname not in [
                "_ElementRenderer",
                "_ElementCompiler",
            ]:
                elder_element_type = cls.__check_elder_element_type()
                cls.__registered_elements[clsmodule][elder_element_type].append(cls)
        super().__init_subclass__(**kwargs)

    @classmethod
    def __check_elder_element_type(cls):
        for basecls in cls.mro():
            if basecls.__name__ == "Message":
                return ElementType.Message
            elif basecls.__name__ == "Service":
                return ElementType.Service
            elif basecls.__name__ == "Enum":
                return ElementType.Enum
        else:
            print(basecls.__name__)
        raise ValueError(f"{cls.__name__} is not a valid ElementType")

    @classmethod
    def __is_user_defined(cls, user_module: str):
        import __main__

        main_path = os.path.dirname(os.path.abspath(__main__.__file__))
        user_module_spec = importlib.util.find_spec(user_module)
        if not user_module_spec or not user_module_spec.origin:
            return False
        user_path = os.path.dirname(os.path.abspath(user_module_spec.origin))
        return user_path.startswith(main_path)


class _ElementRenderer(_ElementRegistry):
    @staticmethod
    def __render_fields(fields):
        rendered_fields = []
        for index, (name, field) in enumerate(
            iterable=fields,
            start=1,
        ):
            origin = get_origin(field.annotation)
            if not origin:
                if field.annotation in _scalar_type_py_to_pb:
                    # 处理有默认值的情况
                    rendered_fields.append(
                        FieldTemplate(
                            name=name,
                            type=_scalar_type_py_to_pb[field.annotation],
                            index=index,
                        ).render()
                    )
                elif issubclass(field.annotation, (Message, Enum)):
                    rendered_fields.append(
                        FieldTemplate(
                            name=name,
                            type=field.annotation.__name__,
                            index=index,
                        ).render()
                    )
                else:
                    raise ValueError(f"Unsupported type: {field.annotation}")
            elif (
                get_origin(field.annotation) == list
                and get_args(field.annotation)[0] in _scalar_type_py_to_pb
            ):
                rendered_fields.append(
                    LabelFieldTemplate(
                        name=name,
                        type=_scalar_type_py_to_pb[get_args(field.annotation)[0]],
                        index=index,
                        label="repeated",
                    ).render()
                )
            elif get_origin(field.annotation) == list and issubclass(
                get_args(field.annotation)[0], (Message, Enum)
            ):
                rendered_fields.append(
                    LabelFieldTemplate(
                        name=name,
                        type=get_args(field.annotation)[0].__name__,
                        index=index,
                        label="repeated",
                    ).render()
                )
            elif (
                get_origin(field.annotation) == dict
                and get_args(field.annotation)[0] in _scalar_type_py_to_pb
            ):
                if get_args(field.annotation)[1] in _scalar_type_py_to_pb:
                    rendered_fields.append(
                        FieldTemplate(
                            name=name,
                            type=f"map<{_scalar_type_py_to_pb[get_args(field.annotation)[0]]}, {_scalar_type_py_to_pb[get_args(field.annotation)[1]]}>",
                            index=index,
                        ).render()
                    )
                elif issubclass(get_args(field.annotation)[1], (Message, Enum)):
                    rendered_fields.append(
                        FieldTemplate(
                            name=name,
                            type=f"map<{_scalar_type_py_to_pb[get_args(field.annotation)[0]]}, {get_args(field.annotation)[1].__name__}>",
                            index=index,
                        ).render()
                    )
            elif get_origin(field.annotation) == typing.Union:
                rendered_oneof_fields = []
                for aindex, arg in enumerate(get_args(field.annotation), start=1):
                    if issubclass(arg, (Message, Enum)):
                        arg_type = arg.__name__
                    elif arg in _scalar_type_py_to_pb:
                        arg_type = _scalar_type_py_to_pb[arg]
                    elif isinstance(None, arg):
                        rendered_oneof_fields.append(
                            FieldTemplate(
                                name=f"{name}_string_optional",
                                type="string",
                                index=index * 1000 + aindex,
                                label="optional",
                            ).render()
                        )
                        continue
                    else:
                        raise ValueError(f"Unsupported type: {arg}")
                    rendered_oneof_fields.append(
                        FieldTemplate(
                            name=f"{name}_{arg_type}",
                            type=arg_type,
                            index=index * 1000 + aindex,
                        ).render()
                    )
                rendered_fields.append(
                    OneOfTemplate(name=name, fields=rendered_oneof_fields).render()
                )
            else:
                raise ValueError(f"Unsupported type: {field.annotation}")
        return rendered_fields

    @staticmethod
    def __render_messages(messages):
        rendered_messages = []
        for message in messages:
            rendered_messages.append(
                MessageTemplate(
                    name=message.__name__,
                    fields=_ElementRenderer.__render_fields(
                        message.__pydantic_fields__.items()
                    ),
                ).render()
            )
        return rendered_messages

    @staticmethod
    def __render_methods(methods):
        rendered_methods = []
        for method in methods:
            annotations = method.__annotations__.copy()
            response = annotations.pop("return")
            request = annotations.popitem()[1]
            rendered_methods.append(
                MethodTemplate(
                    name=method.__name__,
                    request=request.__name__,
                    response=response.__name__,
                ).render()
            )
        return rendered_methods

    @staticmethod
    def __render_services(services):
        rendered_services = []
        for service in services:
            methods = [
                member
                for _, member in service.__dict__.items()
                if inspect.isfunction(member)
            ]
            render_methods = []
            for method in methods:
                if len(method.__annotations__) == 2:
                    annotations = list(method.__annotations__.values())
                    if issubclass(annotations[0], _ElementRegistry) and issubclass(
                        annotations[1], _ElementRegistry
                    ):
                        render_methods.append(method)
            rendered_methods = _ElementRenderer.__render_methods(render_methods)
            rendered_services.append(
                ServiceTemplate(
                    name=service.__name__, methods=rendered_methods
                ).render()
            )
        return rendered_services

    @staticmethod
    def __render_enums(enums):
        rendered_enums = []
        for enum in enums:
            rendered_items = []
            for index, (name, _) in enumerate(
                iterable=enum.__members__.items(),
                start=1,
            ):
                rendered_items.append(EnumItemTemplate(name=name, index=index).render())
            rendered_enums.append(
                EnumTemplate(name=enum.__name__, items=rendered_items).render()
            )
        return rendered_enums

    @staticmethod
    def __render_package(name, elements, imports=[]):
        return PackageTemplate(name=name, imports=imports, elements=elements).render()

    @staticmethod
    def __auto_write_protobuf(module: str, rendered_package: str) -> None:
        spec = importlib.util.find_spec(module)
        if spec is None:
            raise ValueError(f"module {module} not found")
        target = spec.origin
        target = target.replace(".py", ".proto")
        with open(target, "w") as f:
            f.write(rendered_package)

    @classmethod
    def __render(cls, auto_writing: bool = True):
        for (
            module,
            typed_elements,
        ) in cls._ElementRegistry__registered_elements.items():
            messages, services, enums = [], [], []
            for element_type, elements in typed_elements.items():
                if element_type == ElementType.Message:
                    messages = cls.__render_messages(elements)
                elif element_type == ElementType.Service:
                    services = cls.__render_services(elements)
                elif element_type == ElementType.Enum:
                    enums = cls.__render_enums(elements)
                else:
                    raise ValueError(f"Unsupported element type: {element_type}")

            package_name = module.split(".")[-1]
            elements = messages + services + enums
            rendered_package = cls.__render_package(package_name, elements)
            if auto_writing:
                cls.__auto_write_protobuf(module, rendered_package)
            return rendered_package


class _ElementCompiler(_ElementRenderer):
    @classmethod
    def __compile(cls, strict_mode: bool = False, compile_strategy: str = "user"):
        cls._ElementRegistry__register_strategy = compile_strategy
        cls._ElementRenderer__render(auto_writing=True)
        for module in cls._ElementRegistry__registered_elements.keys():
            spec = importlib.util.find_spec(module)
            if not spec:
                raise ValueError(f"module {module} not found")
            target = spec.origin
            target_dir = os.path.dirname(target)
            build_package_protos(
                package_root=target_dir,
                strict_mode=strict_mode,
            )


class ProtobufMixin:
    def to_protobuf(self):
        json_dict = self.model_dump()
        class_path = self.__module__ + "." + self.__class__.__name__
        protobuf_class = importlib.import_module(class_path)
        new_message = protobuf_class()
        return json_format.ParseDict(json_dict, new_message)

    @classmethod
    def from_protobuf(cls, protobuf: typing.Any):
        # 创建一个字典来存储转换后的数据
        data = {}

        # 获取当前类的 pydantic 字段信息
        pydantic_fields = cls.__pydantic_fields__

        # 遍历 protobuf 消息的所有字段
        for field_name, field_type in pydantic_fields.items():
            # 检查 protobuf 是否有这个字段
            if not hasattr(protobuf, field_name):
                continue

            value = getattr(protobuf, field_name)

            # 获取字段的类型信息
            field_annotation = field_type.annotation
            origin = get_origin(field_annotation)

            # 处理不同类型的字段
            if origin is None:
                # 处理基本类型和消息类型
                if issubclass(field_annotation, Message):
                    # 递归处理嵌套的消息
                    data[field_name] = field_annotation.from_protobuf(value)
                elif issubclass(field_annotation, Enum):
                    # 处理枚举类型
                    data[field_name] = field_annotation(value)
                else:
                    # 处理基本类型
                    data[field_name] = value
            elif origin == list:
                # 处理列表类型
                item_type = get_args(field_annotation)[0]
                if issubclass(item_type, Message):
                    data[field_name] = [item_type.from_protobuf(item) for item in value]
                elif issubclass(item_type, Enum):
                    data[field_name] = [item_type(item) for item in value]
                else:
                    data[field_name] = list(value)
            elif origin == dict:
                # 处理字典类型
                key_type, value_type = get_args(field_annotation)
                if issubclass(value_type, Message):
                    data[field_name] = {
                        k: value_type.from_protobuf(v) for k, v in value.items()
                    }
                elif issubclass(value_type, Enum):
                    data[field_name] = {k: value_type(v) for k, v in value.items()}
                else:
                    data[field_name] = dict(value)
            elif origin == typing.Union:
                if value is None:
                    data[field_name] = None
                else:
                    # 获取所有可能的类型（排除 None）
                    possible_types = [
                        t for t in get_args(field_annotation) if t is not type(None)
                    ]

                    # 尝试匹配实际值类型
                    actual_type = type(value)
                    matched_type = None

                    # 首先尝试精确匹配
                    for possible_type in possible_types:
                        if actual_type == possible_type:
                            matched_type = possible_type
                            break

                    # 如果没有精确匹配，尝试继承关系匹配
                    if not matched_type:
                        for possible_type in possible_types:
                            try:
                                if isinstance(value, possible_type):
                                    matched_type = possible_type
                                    break
                            except TypeError:
                                continue

                    # 根据匹配到的类型进行相应转换
                    if matched_type:
                        if issubclass(matched_type, Message):
                            data[field_name] = matched_type.from_protobuf(value)
                        elif issubclass(matched_type, Enum):
                            data[field_name] = matched_type(value)
                        elif matched_type in (int, float, str, bool):
                            data[field_name] = matched_type(value)
                        else:
                            data[field_name] = value
                    else:
                        # 如果没有找到匹配的类型，保持原值
                        data[field_name] = value

        # 使用转换后的数据创建 pydantic 模型实例
        return cls(**data)


class Message(_ElementCompiler, ProtobufMixin, BaseModel):
    pass


class Service(_ElementCompiler):
    def __init_subclass__(cls, **kwargs):
        for name, member in cls.__dict__.items():
            if inspect.isfunction(member):
                annotations = member.__annotations__.copy()
                if len(annotations) == 2:
                    response = annotations.pop("return")
                    request = annotations.popitem()[1]
                    if issubclass(response, _ElementRegistry) and issubclass(
                        request, _ElementRegistry
                    ):
                        setattr(cls, name, cls.__wrap_method(member))
        super().__init_subclass__(**kwargs)

    @staticmethod
    def __wrap_method(method):
        @wraps(method)
        def wrapper(self, request):
            request = request.from_protobuf(request)
            result = method(self, request)
            return result.to_protobuf()

        return wrapper


class Enum(_ElementCompiler, enum.IntEnum):
    pass
