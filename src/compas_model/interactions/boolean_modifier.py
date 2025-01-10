from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep

from .interaction import Interaction


class BooleanModifier(Interaction):
    """Perform boolean difference on the target element.

    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(BooleanModifier, self).__init__(name=name)

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def apply(self, targetgeometry: Union[Brep, Mesh], sourcegeometry: Union[Brep, Mesh]):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : Brep or Mesh
            The geometry to be used as the modifier.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.
        from compas_model.algorithms.modifiers import boolean_difference

        return boolean_difference(targetgeometry, sourcegeometry)
