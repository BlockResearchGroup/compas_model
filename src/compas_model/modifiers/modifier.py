# from typing import Optional
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
        return {}

    def apply(
        self,
        source,
        targetgeometry: Union[Brep, Mesh],
    ) -> Union[Brep, Mesh]:
        """Apply the interaction to the target geometry.

        Parameters
        ----------
        target : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The target of the modification.

        Returns
        -------
        Brep | Mesh
            The modified target geometry.

        """
        raise NotImplementedError
