import numpy as np
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise
from numpy.typing import NDArray

from compas_model.elements import Element


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
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(PlateElement, self).__data__
        data["polygon"] = self.polygon
        data["thickness"] = self.thickness
        data["frame"] = self.frame
        data["name"] = self.name
        data["shape"] = self.shape
        return data

    @classmethod
    def __from_data__(cls, data: dict[str, any]) -> "PlateElement":
        return cls(polygon=data["polygon"], thickness=data["thickness"], frame=data["frame"], name=data["name"], shape=data["shape"])

    def __init__(self, polygon: Polygon, thickness: float, frame: Frame = None, name: str = None, shape=None) -> "PlateElement":
        super(PlateElement, self).__init__(frame=frame, name=name)
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
        self.shape: Mesh = shape if shape else self.compute_shape()
        if not self.name:
            self.name = self.__class__.__name__

    # def __init__(self, bottom: Polygon, top: Polygon, frame: Frame = None, name: str = None, shape: Mesh = None):
    #     super(PlateElement, self).__init__(frame=frame, name=name)
    #     self.bottom: Polygon = bottom
    #     self.top: Polygon = top
    #     self.shape: Mesh = shape if shape else self.compute_shape()
    #     if not self.name:
    #         self.name = self.__class__.__name__

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self) -> Mesh:
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

    def rebuild(self, polygon: Polygon) -> "PlateElement":
        return self
