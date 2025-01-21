from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep

from .modifier import Modifier


class BooleanModifier(Modifier):
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

    def __init__(self, source: Union[Brep, Mesh], name=None):
        # type: (Union[Brep, Mesh], str | None) -> None
        super(BooleanModifier, self).__init__(name=name)
        self.source = source

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def apply(self, target: Union[Brep, Mesh]):
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
        if isinstance(target, Brep) and isinstance(self.source, Brep):
            try:
                return Brep.from_boolean_difference(target, self.source)
            except Exception as e:
                print("Boolean difference is not successful.")
                print(str(e))
                return target
        else:
            from compas_cgal.booleans import boolean_difference_mesh_mesh

            mesh0: Mesh = target.copy() if not isinstance(target, Brep) else Mesh.from_polygons(target.to_polygons())
            mesh1: Mesh = self.source.copy() if not isinstance(self.source, Brep) else Mesh.from_polygons(self.source.to_polygons())

            A = mesh0.to_vertices_and_faces(triangulated=True)
            B = mesh1.to_vertices_and_faces(triangulated=True)

            V, F = boolean_difference_mesh_mesh(A, B)
            mesh: Mesh = Mesh.from_vertices_and_faces(V, F) if len(V) > 0 and len(F) > 0 else mesh0
            return mesh
