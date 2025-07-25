from __future__ import annotations
from functools import wraps
from typing import TypeVar, Callable, TYPE_CHECKING
from enum import Enum

T = TypeVar("T", bound=Enum)

if TYPE_CHECKING:
    from pybantic.main import Pybantic


def enum(
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
        setattr(target_cls, "__pybantic_type__", "enum")
        pb.register(target_cls)
        return target_cls

    return (
        decorator
        if cls is None
        else wraps(cls)(decorator)(
            target_cls=cls,
        )
    )
