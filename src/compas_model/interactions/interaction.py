from typing import Optional

from compas.data import Data


class Interaction(Data):
    """Base class for all types of element-element interactions.

    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self) -> dict:
        return {"name": self.name}

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'
