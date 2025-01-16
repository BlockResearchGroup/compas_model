from typing import Optional
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Plane

from .modifier import Modifier


class SlicerModifier(Modifier):
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

    def __init__(self, slice_plane: Plane, name=None):
        # type: (Union[Brep, Mesh], str | None) -> None
        super(SlicerModifier, self).__init__(name=name)
        self.slice_plane = slice_plane

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def apply(self, targetgeometry: Union[Brep, Mesh]):
        """Cut target geometry by the frame.
        NOTE: If the result is not a valid geometry, the original geometry is returned.

        Parameters
        ----------
        targetgeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.

        try:
            if isinstance(targetgeometry, Brep):
                targetgeometry.make_solid()
                slice_plane_flipped = Plane(self.slice_plane.point, -self.slice_plane.normal)
                targetgeometry.trim(slice_plane_flipped)
                return targetgeometry
            else:
                split_meshes: Optional[list] = targetgeometry.slice(self.slice_plane)
                return split_meshes[0] if split_meshes else targetgeometry
        except Exception:
            print("SlicerModifier is not successful.")
            return targetgeometry
