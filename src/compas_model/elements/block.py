import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import bestfit_frame_numpy
from compas.geometry import bounding_box
from compas.geometry import centroid_points
from compas.geometry import centroid_polyhedron
from compas.geometry import dot_vectors
from compas.geometry import oriented_bounding_box
from compas.geometry import volume_polyhedron
from compas.geometry.brep.brep import Brep

from compas_model.elements import Element
from compas_model.elements import Feature


def invert(self):
    self._yaxis = self._yaxis * -1
    self._zaxis = self._zaxis * -1


Frame.invert = invert


class BlockGeometry(Mesh):
    def face_frame(self, face):
        """Compute the frame of a specific face.

        Parameters
        ----------
        face : int
            The identifier of the frame.

        Returns
        -------
        :class:`compas.geometry.Frame`

        """
        xyz = self.face_coordinates(face)
        normal = self.face_normal(face)
        o, u, v = bestfit_frame_numpy(xyz)
        frame = Frame(o, u, v)
        if frame.zaxis.dot(normal) < 0:
            frame.invert()
        return frame

    def top(self):
        """Identify the *top* face of the block.

        Returns
        -------
        int
            The identifier of the face.

        """
        z = [0, 0, 1]
        faces = list(self.faces())
        normals = [self.face_normal(face) for face in faces]
        return sorted(zip(faces, normals), key=lambda x: dot_vectors(x[1], z))[-1][0]

    def centroid(self):
        """Compute the centroid of the block.

        Returns
        -------
        :class:`compas.geometry.Point`

        """
        x, y, z = centroid_points([self.vertex_coordinates(key) for key in self.vertices()])
        return Point(x, y, z)

    def center(self):
        """Compute the center of mass of the block.

        Returns
        -------
        :class:`compas.geometry.Point`

        """
        vertex_index = {vertex: index for index, vertex in enumerate(self.vertices())}
        vertices = [self.vertex_coordinates(vertex) for vertex in self.vertices()]
        faces = [[vertex_index[vertex] for vertex in self.face_vertices(face)] for face in self.faces()]
        x, y, z = centroid_polyhedron((vertices, faces))
        return Point(x, y, z)

    def volume(self):
        """Compute the volume of the block.

        Returns
        -------
        float
            The volume of the block.

        """
        vertex_index = {vertex: index for index, vertex in enumerate(self.vertices())}
        vertices = [self.vertex_coordinates(vertex) for vertex in self.vertices()]
        faces = [[vertex_index[vertex] for vertex in self.face_vertices(face)] for face in self.faces()]
        v = volume_polyhedron((vertices, faces))
        return v


# A block could have features like notches,
# but we will work on it when we need it...
# A notch could be a cylinder defined in the frame of a face.
# The frame of a face should be defined in coorination with the global frame of the block.
# during interface detection the features could/should be ignored.
class BlockFeature(Feature):
    pass


class BlockElement(Element):
    """Class representing block elements.

    Parameters
    ----------
    shape : :class:`compas.datastructures.Mesh`
        The base shape of the block.
    features : list[:class:`BlockFeature`], optional
        Additional block features.
    is_support : bool, optional
        Flag indicating that the block is a support.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`BlockFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    elementgeometry: BlockGeometry
    modelgeometry: BlockGeometry

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["shape"] = self.shape
        data["features"] = self.features
        data["is_support"] = self.is_support
        return data

    def __init__(self, shape, features=None, is_support=False, frame=None, transformation=None, name=None):
        # type: (Mesh | BlockGeometry, list[BlockFeature] | None, bool, compas.geometry.Frame | None, compas.geometry.Transformation | None, str | None) -> None
        super().__init__(frame=frame, transformation=transformation, name=name)

        self.shape = shape if isinstance(shape, BlockGeometry) else shape.copy(cls=BlockGeometry)
        self.features = features or []  # type: list[BlockFeature]
        self.is_support = is_support

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_elementgeometry(self) -> Mesh | Brep:
        geometry = self.shape
        # apply features?
        return geometry

    def compute_modelgeometry(self) -> Mesh | Brep:
        if not self.model:
            raise Exception

        geometry = self.elementgeometry.transformed(self.modeltransformation)

        # apply effect of interactions?
        node = self.graphnode
        nbrs = self.model.graph.neighbors_in(node)
        for nbr in nbrs:
            element = self.model.graph.node_element(nbr)
            if element:
                for interaction in self.model.graph.edge_interactions((nbr, node)):
                    # example interactions are
                    # cutters, boolean operations, slicers, ...
                    if hasattr(interaction, "apply"):
                        try:
                            interaction.apply(geometry)
                        except Exception:
                            pass

        return geometry

    def compute_aabb(self, inflate=0.0):
        points = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0):
        points = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self):
        # TODO: (TvM) make this a pluggable with default implementation in core and move import to top
        from compas.geometry import convex_hull_numpy

        points = self.modelgeometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    @classmethod
    def from_box(cls, box):
        # type: (compas.geometry.Box) -> BlockElement
        shape = box.to_mesh()
        block = cls(shape=shape)
        return block
