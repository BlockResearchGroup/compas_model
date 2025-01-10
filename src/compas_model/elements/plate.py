from typing import Optional

import numpy as np
from numpy.typing import NDArray

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise
from compas_model.elements import Element
from compas_model.elements import Feature


class PlateFeature(Feature):
    pass


class PlateElement(Element):
    """Class representing a block element.

    Parameters
    ----------
    polygon : :class:`compas.geometry.Polygon`
        The base polygon of the plate.
    thickness : float
        The total offset thickness above and blow the polygon
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.
    shape : :class:`compas.datastructures.Mesh`, optional
        The base shape of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self) -> dict:
        return {
            "polygon": self.polygon,
            "thickness": self.thickness,
            "is_support": self.is_support,
            "frame": self.frame,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        polygon: Polygon = Polygon.from_sides_and_radius_xy(4, 1.0),
        thickness: float = 0.1,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[PlateFeature]] = None,
        name: Optional[str] = None,
    ) -> "PlateElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)
        self.is_support: bool = is_support
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

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

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

    def compute_aabb(self, inflate: float = 0.0) -> Box:
        points: list[Point] = self.geometry.vertices_attributes("xyz")
        box: Box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate: float = 0.0) -> Box:
        points: list[Point] = self.geometry.vertices_attributes("xyz")
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        from compas.geometry import convex_hull_numpy

        points: list[Point] = self.geometry.vertices_attributes("xyz")
        faces: NDArray[np.intc] = convex_hull_numpy(points)
        vertices: list[Point] = [points[index] for index in range(len(points))]
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================
