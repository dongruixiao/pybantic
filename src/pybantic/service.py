from __future__ import annotations
import inspect
from functools import wraps
import os
from pydantic import BaseModel
from typing import TYPE_CHECKING, Callable, TypeAlias, TypeVar
from google.protobuf.message import Message

if TYPE_CHECKING:
    from pybantic.main import Pybantic


T = TypeVar("T")

ModelRequest = TypeVar("ModelRequest", bound=BaseModel)
ModelResponse = TypeVar("ModelResponse", bound=BaseModel)
MessageRequest: TypeAlias = Message
MessageResponse: TypeAlias = Message


def service(
    cls: type[T] | None = None,
    /,
    *,
    pb: Pybantic,
) -> (
    type[T]
    | Callable[
        [type[T]],
        type[T],
    ]
):

    def decorator(target_cls: type[T]) -> type[T]:
        # target_cls_file_path = inspect.getabsfile(target_cls)
        # __pb2_output_dir__ = os.path.dirname(target_cls_file_path)
        # __pb2_output_file__ = os.path.basename(target_cls_file_path)

        # setattr(target_cls, "__pb2_output_dir__", __pb2_output_dir__)
        # setattr(target_cls, "__pb2_output_file__", __pb2_output_file__)
        setattr(target_cls, "__pybantic_type__", "service")
        pb.register(target_cls)

        return target_cls

    return (
        decorator
        if cls is None
        else wraps(cls)(decorator)(
            target_cls=cls,
        )
    )


def expose(
    method: Callable[[T, ModelRequest], ModelResponse],
) -> Callable[
    [T, ModelRequest],
    ModelResponse,
]:
    parameters = inspect.signature(method).parameters

    assert len(parameters) == 2, (
        f"method {method.__qualname__} must have two parameters: "
        f"`self: T` and `request: ModelRequest`"
    )

    parameter_keys = list(parameters.keys())

    assert "self" == parameter_keys[0], (
        f"`self` must be a class instance of type `T` "
        f"at the first parameter of method "
        f"`{method.__qualname__}`"
    )
    assert "request" == parameter_keys[1], (
        f"`request` must be a Pydantic model "
        f"at the second parameter of method "
        f"`{method.__qualname__}`"
    )

    # setattr(method, "__expose_as_rpc_interface__", True)
    # return method
    @wraps(method)
    def wrapper(self: T, request: ModelRequest) -> ModelResponse:
        return method(self, request)

    setattr(wrapper, "__expose_as_rpc_interface__", True)
    return wrapper
