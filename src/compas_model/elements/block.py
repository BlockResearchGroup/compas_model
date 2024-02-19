from compas_model.elements import Element
from compas.datastructures import Mesh
from compas.geometry import convex_hull_numpy
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.geometry import Box
from compas.geometry import Frame  # noqa: F401

# from compas.geometry import Polygon


class BlockElement(Element):
    """Block element model.

    Parameters
    ----------
    geometry : :class:`compas.datastructures.Mesh`
        The geometry of the block.
    is_support : bool, optional
        Flag indicating that the block is a support.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(BlockElement, self).__data__
        data["is_support"] = self.is_support
        return data

    @classmethod
    def __from_data__(cls, data):
        # type: (dict) -> BlockElement
        return cls(**data)

    def __init__(self, geometry, is_support=False, frame=None, name=None):
        # type: (Mesh, bool | None, Frame | None, str | None) -> None
        super(BlockElement, self).__init__(geometry=geometry, frame=frame, name=name)
        self.is_support = is_support

    # @property
    # def face_polygons(self):
    #     points_lists = self.geometry.to_polygons()
    #     return [Polygon(points) for points in points_lists]

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

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
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    def transform(self, transformation):
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self.geometry.transform(transformation)
