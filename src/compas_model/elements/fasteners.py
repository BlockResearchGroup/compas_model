from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Vector
from compas.geometry import bounding_box
from compas.geometry import intersection_line_plane
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise

from .element import Element
from .element import Feature


class FastenersElement(Element):
    """Class representing a fastener: screw, dowel, bolt and etc."""


class FastenersFeature(Feature):
    pass


class ScrewElement(Element):
    """Class representing a screw, dowel, or pin.

    Parameters
    ----------
    radius : float
        Radius of the screw.
    sides : int
        Number of sides of the screw's polygonal section.
    length : float
        Length of the screw.
    frame : :class:`compas.geometry.Frame`
        Main frame of the screw.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the screw.
    features : Optional[list[:class:`compas_model.features.FastenersFeature`]]
        Features of the screw.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    axis : :class:`compas.geometry.Vector`
        Line axis of the screw.
    section : :class:`compas.geometry.Polygon`
        Section polygon of the screw.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the screw.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the screw.
    """

    @property
    def __data__(self) -> dict:
        return {
            "radius": self.radius,
            "sides": self.sides,
            "length": self.length,
            "frame": self.frame,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        radius: float = 0.4,
        sides: int = 6,
        length: float = 3.0,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[FastenersFeature]] = None,
        name: Optional[str] = None,
    ) -> "ScrewElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.radius = radius
        self.sides = sides
        self.length = length
        self.axis: Vector = Line([0, 0, 0], [0, 0, length]).vector
        self.section: Polygon = Polygon.from_sides_and_radius_xy(sides, radius)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length

        # Create the polygon of the I profile
        self.section = Polygon(list(self.points)).translated([0, 0, 0.5 * length])

        self.axis = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    def compute_top_and_bottom_polygons(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the column.

        Returns
        -------
        tuple[:class:`compas.geometry.Polygon`, :class:`compas.geometry.Polygon`]
        """

        plane0: Plane = Plane.from_frame(Frame(self.frame.point - self.axis * 0.5, self.frame.xaxis, self.frame.yaxis))
        plane1: Plane = Plane.from_frame(Frame(self.frame.point + self.axis * 0.5, self.frame.xaxis, self.frame.yaxis))
        points0: list[list[float]] = []
        points1: list[list[float]] = []
        for i in range(len(self.section.points)):
            line: Line = Line(self.section.points[i], self.section.points[i] + self.axis)
            result0: Optional[list[float]] = intersection_line_plane(line, plane0)
            result1: Optional[list[float]] = intersection_line_plane(line, plane1)
            if not result0 or not result1:
                raise ValueError("The line does not intersect the plane")
            points0.append(result0)
            points1.append(result1)
        return Polygon(points0), Polygon(points1)

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the column from the given polygons.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """

        offset: int = len(self.polygon_bottom)
        vertices: list[Point] = self.polygon_bottom.points + self.polygon_top.points  # type: ignore
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
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The axis-aligned bounding box.
        """
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate: float = 0.0) -> Box:
        """Compute the oriented bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        :class:`compas.geometry.Box`
            The oriented bounding box.
        """
        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        box: Box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        from compas.geometry import convex_hull_numpy

        points: list[list[float]] = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================
