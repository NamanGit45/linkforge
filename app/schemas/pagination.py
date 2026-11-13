# app/schemas/pagination.py
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):

    items: list[T]
    total: int
    limit: int
    offset: int


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None  # None means: no more pages
    limit: int
