from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.itertools import pairwise
from compas_model.elements.element import Element
from compas_model.elements.element import Feature


class PlateFeature(Feature):
    pass


class PlateElement(Element):
    """Class representing a plate element constructed from a polygon and thickness.
    The polygon is extruded in the opposite direction of the polygon normal.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The base polygon of the plate.
    thickness : float
        The total offset thickness above and blow the polygon
    transformation : :class:`compas.geometry.Transformation`, optional
        The transformation of the plate.
    features : list[:class:`PlateFeature`], optional
        The features of the plate.
    name : str, optional
        The name of the plate.

    Attributes
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The base polygon of the plate.
    bottom : :class:`compas.geometry.Polygon`
        The base polygon of the plate.
    top : :class:`compas.geometry.Polygon`
        The top polygon of the plate.
    thickness : float
        The total offset thickness above and blow the polygon

    """

    @property
    def __data__(self) -> dict:
        return {
            "polygon": self.polygon,
            "thickness": self.thickness,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        polygon: Polygon = Polygon.from_sides_and_radius_xy(4, 1.0),
        thickness: float = 0.1,
        transformation: Optional[Transformation] = None,
        features: Optional[list[PlateFeature]] = None,
        name: Optional[str] = None,
    ) -> "PlateElement":
        super().__init__(transformation=transformation, features=features, name=name)
        self.polygon: Polygon = polygon
        self.thickness: float = thickness
        normal: Vector = polygon.normal
        down: Vector = normal * (0.0 * thickness)
        up: Vector = normal * (-1.0 * thickness)
        self.bottom: Polygon = polygon.copy()
        for point in self.bottom.points:
            point += down
        self.top: Polygon = polygon.copy()
        for point in self.top.points:
            point += up

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the plate from the given polygons.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        offset: int = len(self.bottom)
        vertices: list[Point] = self.bottom.points + self.top.points  # type: ignore
        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        faces: list[list[int]] = [bottom[::-1], top]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([a, b, d, c])
        mesh: Mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_aabb(self) -> Box:
        box = self.modelgeometry.aabb
        if self.inflate_aabb and self.inflate_aabb != 1.0:
            box.xsize += self.inflate_aabb
            box.ysize += self.inflate_aabb
            box.zsize += self.inflate_aabb
        self._aabb = box
        return box

    def compute_obb(self) -> Box:
        box = self.modelgeometry.obb
        if self.inflate_aabb and self.inflate_aabb != 1.0:
            box.xsize += self.inflate_obb
            box.ysize += self.inflate_obb
            box.zsize += self.inflate_obb
        self._obb = box
        return box

    def compute_collision_mesh(self) -> Mesh:
        mesh = self.modelgeometry
        self._collision_mesh = mesh
        return mesh

    def compute_point(self) -> Point:
        return Point(*self.modelgeometry.centroid())
