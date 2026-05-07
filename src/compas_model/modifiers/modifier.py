from typing import TYPE_CHECKING
from typing import Union

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Brep

if TYPE_CHECKING:
    from compas_model.elements import Element


class Modifier(Data):
    """Base class for element-element modifiers."""

    @property
    def __data__(self) -> dict:
        return {}

    def apply(
        self,
        source: "Element",
        targetgeometry: Union[Brep, Mesh],
    ) -> Union[Brep, Mesh]:
        """Apply the interaction from a source element to a target geometry.

        Parameters
        ----------
        source
            The source element.
        targetgeometry
            The target geometry of the modification.

        Returns
        -------
        Brep | Mesh
            The modified target geometry.

        """
        raise NotImplementedError
