import compas.datastructures  # noqa: F401
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box

from compas_model.elements import Element
from compas_model.elements import Feature


class InterfaceFeature(Feature):
    pass


class InterfaceElement(Element):
    """Class representing a phyisical interface between two other elements.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        A polygon that represents the outline of the interface.
    thickness : float
        The thickness of the interface.
    features : list[:class:`InterfaceFeature`], optional
        Additional interface features.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the interface.
    features : list[:class:`BlockFeature`]
        A list of additional interface features.

    Notes
    -----
    The shape of the interface is calculated automatically from the input polygon and thickness.
    The frame of the element is the frame of the polygon.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(InterfaceElement, self).__data__
        return data

    def __init__(self, polygon, thickness, features=None, frame=None, name=None):
        # type: (compas.geometry.Polygon, float, list[InterfaceFeature] | None, compas.geometry.Frame | None, str | None) -> None

        frame = frame or polygon.frame

        super(InterfaceElement, self).__init__(frame=frame, name=name)
        self._polygon = polygon
        self._thickness = thickness
        self.shape = self.compute_shape()
        self.features = features or []  # type: list[InterfaceFeature]

    def compute_shape(self):
        # type: () -> compas.datastructures.Mesh
        mesh = Mesh.from_polygons([self._polygon])
        return mesh.thickened(self._thickness)

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
        from compas.geometry import convex_hull_numpy

        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)
