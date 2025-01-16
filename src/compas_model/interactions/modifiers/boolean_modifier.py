from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep

from .modifier import Modifier


class BooleanModifier(Modifier):
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

    def apply(self, target_geometry: Union[Brep, Mesh]):
        """Apply the interaction to the affected geometry.
        NOTE: If the result is not a valid geometry, the original geometry is returned.

        Parameters
        ----------
        targetgeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be used as the modifier.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.
        if isinstance(target_geometry, Brep) and isinstance(self.cutter, Brep):
            try:
                return Brep.from_boolean_difference(target_geometry, self.cutter)
            except Exception:
                print("Boolean difference is not successful.")
                return target_geometry
        else:
            from compas_cgal.booleans import boolean_difference_mesh_mesh

            mesh0: Mesh = target_geometry.copy() if not isinstance(target_geometry, Brep) else Mesh.from_polygons(target_geometry.to_polygons())
            mesh1: Mesh = self.cutter.copy() if not isinstance(self.cutter, Brep) else Mesh.from_polygons(self.cutter.to_polygons())
            print(mesh0)
            print(mesh1)
            A = mesh0.to_vertices_and_faces(triangulated=True)
            B = mesh1.to_vertices_and_faces(triangulated=True)

            V, F = boolean_difference_mesh_mesh(A, B)
            mesh: Mesh = Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else mesh0
            return mesh
