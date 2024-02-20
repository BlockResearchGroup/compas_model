import compas.geometry
import compas.datastructures  # noqa: F401
from compas_model.elements import Element
from compas_model.elements import Feature  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import convex_hull_numpy
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.geometry import Box
from compas.geometry import Frame  # noqa: F401


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

    @classmethod
    def __from_data__(cls, data):
        # type: (dict) -> BlockElement
        return cls(**data)

    def __init__(self, shape, features=None, is_support=False, frame=None, name=None):
        # type: (Mesh, list[BlockFeature] | None, bool, Frame | None, str | None) -> None

        super(BlockElement, self).__init__(frame=frame, name=name)
        self.shape = shape
        self.features = features or []
        self.is_support = is_support

    # don't like this
    # needs to go
    # but want to test the collider
    @property
    def face_polygons(self):
        # points_lists = self.geometry.to_polygons()
        # return [Polygon(points) for points in points_lists]
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
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # def transform(self, transformation):
    #     self._aabb = None
    #     self._obb = None
    #     self._collision_mesh = None
    #     # self.geometry.transform(transformation)
