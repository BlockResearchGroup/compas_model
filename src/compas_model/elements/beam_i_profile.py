from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import bounding_box
from compas.geometry import intersection_line_plane
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise

from compas_model.elements import Element
from compas_model.elements import Feature


class BeamIProfileFeature(Feature):
    pass


class BeamIProfileElement(Element):
    """Class representing a beam element with I profile.

    Parameters
    ----------
    width : float, optional
        The width of the beam.
    depth : float, optional
        The depth of the beam.
    thickness : float, optional
        The thickness of the beam.
    length : float, optional
        The length of the beam.
    frame_bottom : :class:`compas.geometry.Plane`, optional
        The frame of the bottom polygon.
    frame_top : :class:`compas.geometry.Plane`, optional
        The frame of the top polygon.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    axis : :class:`compas.geometry.Line`
        The axis of the beam.
    section : :class:`compas.geometry.Polygon`
        The section of the beam.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the beam.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the beam.
    transformation : :class:`compas.geometry.Transformation`
        The transformation applied to the beam.
    material : :class:`compas_model.Material`
        The material of the beam.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "depth": self.depth,
            "thickness": self.thickness,
            "length": self.length,
            "frame_top": self.frame_top,
            "is_support": self.is_support,
            "frame": self.frame,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.1,
        depth: float = 0.2,
        thickness: float = 0.02,
        length: float = 3.0,
        frame_top: Optional[Plane] = None,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamIProfileFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamIProfileElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = width
        self.depth: float = depth
        self.thickness: float = thickness
        self.length: float = length

        p0: list[float] = [0, -self.depth * 0.5, 0]
        p1: list[float] = [0, self.depth * 0.5, 0]

        p2: list[float] = [-self.thickness, self.depth * 0.5, 0]
        p3: list[float] = [-self.thickness, self.thickness * 0.5, 0]
        p4: list[float] = [-self.width + self.thickness, self.thickness * 0.5, 0]
        p5: list[float] = [-self.width + self.thickness, self.depth * 0.5, 0]

        p6: list[float] = [-self.width, self.depth * 0.5, 0]
        p7: list[float] = [-self.width, -self.depth * 0.5, 0]
        p8: list[float] = [-self.width + self.thickness, -self.depth * 0.5, 0]
        p9: list[float] = [-self.width + self.thickness, -self.thickness * 0.5, 0]
        p10: list[float] = [-self.thickness, -self.thickness * 0.5, 0]
        p11: list[float] = [-self.thickness, -self.depth * 0.5, 0]

        # Create the polygon of the I profile
        self.section: Polygon = Polygon([p0, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11]).translated([0, 0, 0.5 * length])

        self.axis: Line = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

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

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the beam from the given polygons .
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

    def rebuild(self, length: float) -> "BeamIProfileElement":
        """Rebuild the column with a new length.

        Parameters
        ----------
        length : float
            The new length of the column.

        Returns
        -------
        :class:`ColumnSquareElement`
            The new column element.
        """
        return BeamIProfileElement(width=self.width, depth=self.depth, thickness=self.thickness, length=length)
