from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Plane

from .modifier import Modifier


class SlicerModifier(Modifier):
    """Perform boolean difference on the target element.

    Parameters
    ----------
    source : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
        The geometry to be used as the modifier
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name, "source": self.source}

    def __init__(self, slice_plane: Plane, name=None):
        # type: (Union[Brep, Mesh], str | None) -> None
        super(SlicerModifier, self).__init__(name=name)
        self.slice_plane = slice_plane

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def apply(self, target: Union[Brep, Mesh]):
        """Cut target geometry by the frame.
        NOTE: If the result is not a valid geometry, the original geometry is returned.

        Parameters
        ----------
        target : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.

        try:
            if isinstance(target, Brep):
                target.make_solid()
                slice_plane_flipped = Plane(self.slice_plane.point, -self.slice_plane.normal)
                target.trim(slice_plane_flipped)
                return target
            else:
                split_meshes: list[Mesh] = target.slice(self.slice_plane)
                return split_meshes[0] if split_meshes else target
        except Exception as e:
            print("SlicerModifier is not successful.")
            print(str(e))
            return target
