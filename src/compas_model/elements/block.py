import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import bounding_box
from compas.geometry import centroid_points
from compas.geometry import centroid_polyhedron
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.geometry import oriented_bounding_box
from compas.geometry import volume_polyhedron

from compas_model.elements import Element
from compas_model.elements import Feature


class BlockGeometry(Mesh):
    def centroid(self):
        """Compute the centroid of the block.

        Returns
        -------
        :class:`compas.geometry.Point`

        """
        x, y, z = centroid_points([self.vertex_coordinates(key) for key in self.vertices()])
        return Point(x, y, z)

    def frames(self):
        """Compute the local frame of each face of the block.

        Returns
        -------
        dict
            A dictionary mapping face identifiers to face frames.

        """
        return {face: self.frame(face) for face in self.faces()}

    def frame(self, face):
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
        o = self.face_center(face)
        w = self.face_normal(face)
        u = [xyz[1][i] - xyz[0][i] for i in range(3)]  # align with longest edge instead?
        v = cross_vectors(w, u)
        return Frame(o, u, v)

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

    @property
    def __data__(self):
        # type: () -> dict
        data = super(BlockElement, self).__data__
        data["shape"] = self.shape
        data["features"] = self.features
        data["is_support"] = self.is_support
        return data

    def __init__(self, shape, features=None, is_support=False, frame=None, transformation=None, name=None):
        # type: (Mesh | BlockGeometry, list[BlockFeature] | None, bool, compas.geometry.Frame | None, compas.geometry.Transformation | None, str | None) -> None

        super(BlockElement, self).__init__(frame=frame, transformation=transformation, name=name)
        self.shape = shape if isinstance(shape, BlockGeometry) else shape.copy(cls=BlockGeometry)
        self.features = features or []  # type: list[BlockFeature]
        self.is_support = is_support

    # don't like this
    # but want to test the collider
    @property
    def face_polygons(self):
        # type: () -> list[compas.geometry.Polygon]
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_geometry(self, include_features=False):
        geometry = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self):
        # TODO: (TvM) make this a pluggable with default implementation in core and move import to top
        from compas.geometry import convex_hull_numpy

        points = self.geometry.vertices_attributes("xyz")  # type: ignore
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
