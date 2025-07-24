from __future__ import annotations
from functools import wraps
from typing import TypeVar, Callable, TYPE_CHECKING
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

if TYPE_CHECKING:
    from pybantic.main import Pybantic


def message(
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
        setattr(target_cls, "__pybantic_type__", "message")
        pb.register(target_cls)
        return target_cls

    return (
        decorator
        if cls is None
        else wraps(cls)(decorator)(
            target_cls=cls,
        )
    )


if __name__ == "__main__":

    pb = Pybantic()

    @message(pb=pb)
    class A(BaseModel):
        a: int
        b: str

    print(A)

    @message(pb=pb)
    class B(BaseModel):
        c: int
        d: str

    print(B)
