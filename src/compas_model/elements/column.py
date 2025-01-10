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


class ColumnFeature(Feature):
    pass


class ColumnElement(Element):
    """Class representing a beam element."""

    pass


class ColumnSquareElement(ColumnElement):
    """Class representing a column element with a square section.

    Parameters
    ----------
    width : float
        The width of the column.
    depth : float
        The depth of the column.
    height : float
        The height of the column.
    frame_bottom : :class:`compas.geometry.Frame`
        Main frame of the column.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the column that is used to cut the second end, while the first frame is used to cut the first end.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the column.
    features : Optional[list[:class:`compas_model.features.ColumnFeature`]]
        Features of the column.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    width : float
        The width of the column.
    depth : float
        The depth of the column.
    height : float
        The height of the column.
    is_support : bool
        Flag indicating if the column is a support.
    frame_bottom : :class:`compas.geometry.Frame`
        Main frame of the column.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the column.
    transformation : :class:`compas.geometry.Transformation`
        Transformation applied to the column.
    features : list[:class:`compas_model.features.ColumnFeature`]
        Features of the column.
    name : str
        The name of the column.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "frame_top": self.frame_top,
            "is_support": self.is_support,
            "frame": self.frame,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.4,
        depth: float = 0.4,
        height: float = 3.0,
        frame_top: Optional[Plane] = None,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[ColumnFeature]] = None,
        name: Optional[str] = None,
    ) -> "ColumnSquareElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width = width
        self.depth = depth
        self._height = height
        self.axis: Line = Line([0, 0, 0], [0, 0, height])
        p3: list[float] = [-width * 0.5, -depth * 0.5, 0]
        p2: list[float] = [-width * 0.5, depth * 0.5, 0]
        p1: list[float] = [width * 0.5, depth * 0.5, 0]
        p0: list[float] = [width * 0.5, -depth * 0.5, 0]
        self.section: Polygon = Polygon([p0, p1, p2, p3])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, height: float):
        self._height = height
        self.axis: Line = Line([0, 0, 0], [0, 0, self._height])
        self.frame_top: Frame = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_top_and_bottom_polygons(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the column.

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


class ColumnRoundElement(ColumnElement):
    """Class representing a column element with a round section.

    Parameters
    ----------
    radius : float
        Radius of the column.
    sides : int
        Number of sides of the column's polygonal section.
    height : float
        Height of the column.
    frame_top : Optional[:class:`compas.geometry.Plane`]
        Second frame of the column that is used to cut the second end, while the first frame is used to cut the first end.
    is_support : bool
        Flag indicating if the column is a support.
    frame : :class:`compas.geometry.Frame`
        Main frame of the column.
    transformation : Optional[:class:`compas.geometry.Transformation`]
        Transformation applied to the column.
    features : Optional[list[:class:`compas_model.features.ColumnFeature`]]
        Features of the column.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    radius : float
        Radius of the column.
    sides : int
        Number of sides of the column's polygonal section.
    height : float
        Height of the column.
    is_support : bool
        Flag indicating if the column is a support.
    frame : :class:`compas.geometry.Frame`
        Main frame of the column.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the column.
    axis : :class:`compas.geometry.Line`
        Line axis of the column.
    section : :class:`compas.geometry.Polygon`
        Section polygon of the column.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the column.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the column.
    transformation : :class:`compas.geometry.Transformation`
        Transformation applied to the column.
    features : list[:class:`compas_model.features.ColumnFeature`]
        Features of the column.
    name : str
        The name of the column.
    """

    @property
    def __data__(self) -> dict:
        return {
            "radius": self.radius,
            "sides": self.sides,
            "height": self.height,
            "frame_top": self.frame_top,
            "is_support": self.is_support,
            "frame": self.frame,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        radius: float = 0.4,
        sides: int = 24,
        height: float = 3.0,
        frame_top: Optional[Plane] = None,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[ColumnFeature]] = None,
        name: Optional[str] = None,
    ) -> "ColumnRoundElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.radius = radius
        self.sides = sides
        self._height = height
        self.axis: Line = Line([0, 0, 0], [0, 0, self._height])
        self.section: Polygon = Polygon.from_sides_and_radius_xy(sides, radius)
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def face_polygons(self) -> list[Polygon]:
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, height: float):
        self._height = height
        self.axis: Line = Line([0, 0, 0], [0, 0, self._height])
        self.frame_top: Frame = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    def compute_top_and_bottom_polygons(self) -> tuple[Polygon, Polygon]:
        """Compute the top and bottom polygons of the column.

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
