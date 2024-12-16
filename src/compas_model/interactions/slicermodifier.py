from compas.geometry import Plane  # noqa: F401

from compas_model.algorithms.modifiers import slice  # noqa: F401

from .interaction import Interaction


class SlicerModifier(Interaction):
    """Base class for all types of element-element interactions.

    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name, "slice_plane": self.slice_plane}

    def __init__(self, plane, name=None):
        # type: (Plane, str | None) -> None
        super(SlicerModifier, self).__init__(name=name)
        self.slice_plane = plane  # Virtual geometry are stored in interaction.

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def modify(self, targetgeometry, targetelement, _):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        targetelement : Element
            The element that is modified.
        """

        return slice(targetgeometry, self.slice_plane.transformed(targetelement.modeltransformation))
