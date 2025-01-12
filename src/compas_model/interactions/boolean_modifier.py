from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep

from .interaction import Interaction


class BooleanModifier(Interaction):
    """Perform boolean difference on the target element.

    Parameters
    ----------
    cutter : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry to be used as the modifier
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name, "cutter": self.cutter}

    def __init__(self, cutter: Union[Brep, Mesh], name=None):
        # type: (Union[Brep, Mesh], str | None) -> None
        super(BooleanModifier, self).__init__(name=name)
        self.cutter = cutter

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def apply(self, targetgeometry: Union[Brep, Mesh]):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be used as the modifier.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.
        from compas_model.algorithms.modifiers import boolean_difference

        return boolean_difference(targetgeometry, self.cutter)
