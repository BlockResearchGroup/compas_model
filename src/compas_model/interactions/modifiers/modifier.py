from typing import Optional
from typing import Union

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Brep


class Modifier(Data):
    """Base class for element-element modifiers.

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

    def __repr__(self):
        return f'{self.__class__.__name__}(name="{self.name}")'

    def apply(self, source: Union[Brep, Mesh], target: Union[Brep, Mesh]):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        source : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The source of the modification.
        target : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The target of the modification.

        """
        raise NotImplementedError
