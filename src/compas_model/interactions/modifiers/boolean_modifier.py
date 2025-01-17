from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep

from .modifier import Modifier


class BooleanModifier(Modifier):
    """Class representing a modifier that performs a boolean operation on a target geometry.

    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

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
