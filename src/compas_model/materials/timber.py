from typing import Optional

from .material import Material


class Timber(Material):
    @property
    def __data__(self) -> dict:
        data = super().__data__
        return data

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)
