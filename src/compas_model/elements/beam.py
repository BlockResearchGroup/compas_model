from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import bounding_box
from compas.geometry import identity_matrix
from compas.geometry import intersection_line_plane
from compas.geometry import oriented_bounding_box
from compas_model.elements.element import Element
from compas_model.elements.element import Feature


class BeamFeature(Feature):
    pass


class BeamElement(Element):
    """Class representing a beam element with a square section, constructed from WorldXY Frame.

    Parameters
    ----------
    width : float
        The width of the beam.
    depth : float
        The depth of the beam.
    length : float
        The length of the beam.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the beam.
    features : Optional[list[:class:`compas_model.features.BeamFeature`]]
        Features of the beam.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    width : float
        The width of the beam.
    depth : float
        The depth of the beam.
    length : float
        The length of the beam.
    is_support : bool
        Flag indicating if the beam is a support.
    frame_bottom : :class:`compas.geometry.Frame`
        Main frame of the beam.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the beam.
    axis : :class:`compas.geometry.Line`
        Line axis of the beam.
    section : :class:`compas.geometry.Polygon`
        Section polygon of the beam.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the beam.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the beam.
    transformation : :class:`compas.geometry.Transformation`
        Transformation applied to the beam.
    features : list[:class:`compas_model.features.BeamFeature`]
        Features of the beam.
    name : str
        The name of the beam.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "depth": self.depth,
            "length": self.length,
            "is_support": self.is_support,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.1,
        depth: float = 0.2,
        length: float = 3.0,
        is_support: bool = False,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamElement":
        super().__init__(frame=Frame.worldXY(), transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = width
        self.depth: float = depth
        self._length: float = length

        self.points: list[list[float]] = [[-width * 1, -depth * 0.5, 0], [-width * 1, depth * 0.5, 0], [width * 0, depth * 0.5, 0], [width * 0, -depth * 0.5, 0]]

        self.section: Polygon = Polygon(self.points)
        self.axis: Line = Line([0, 0, 0], [0, 0, length])
        self.frame_top: Frame = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the beam from the given polygons .
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        box: Box = Box.from_width_height_depth(self.width, self.length, self.depth)
        box.translate(
            [
                self.width * -0.5,
                0,
                self.length * 0.5,
            ]
        )
        return box.to_mesh()

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length

        self.section = Polygon(list(self.points))

        self.axis = Line([0, 0, 0], [0, 0, length])
        self.frame_top = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance : float
            The distance to extend the beam.
        """
        self.length = self.length + distance * 2
        xform: Transformation = Translation.from_vector([0, 0, -distance])
        self.transformation = self.transformation * xform

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

    def compute_point(self) -> Point:
        """Computes a reference point for the element geometry (e.g. the centroid).

        Returns
        -------
        :class:`compas.geometry.Point`
            The reference point.

        """

        xform: Transformation = identity_matrix if self.modeltransformation is None else self.modeltransformation
        return self.frame.point.transformed(xform)

    def compute_top_and_bottom_polygons(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the beam.

        Returns
        -------
        tuple[:class:`compas.geometry.Polygon`, :class:`compas.geometry.Polygon`]
        """

        plane0: Plane = Plane.from_frame(self.frame)
        plane1: Plane = Plane.from_frame(self.frame_top)
        points0: list[list[float]] = []
        points1: list[list[float]] = []
        for i in range(len(self.section.points)):
            line: Line = Line(self.section.points[i], self.section.points[i] + self.axis.vector)
            result0: Optional[list[float]] = intersection_line_plane(line, plane0)
            result1: Optional[list[float]] = intersection_line_plane(line, plane1)
            if not result0 or not result1:
                raise ValueError("The line does not intersect the plane")
            points0.append(result0)
            points1.append(result1)
        return Polygon(points0), Polygon(points1)
