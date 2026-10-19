from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class LimitOffsetResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = 0
    limit: int
    offset: int
