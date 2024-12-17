from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bounding_box
from compas.geometry import intersection_line_plane
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise

from compas_model.elements import Element


class ColumnSquareElement(Element):
    """Class representing a column element with a square-section.

    Parameters
    ----------
    width : float
        Width of column.
    depth : float
        Depth of a column.
    height : float
        Height of a column.
    frame_bottom : :class:`compas.geometry.Frame`
        Main frame of the column.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the column that is used to cut the the second end, while the first frame is used to cut the first end.
    name : str
        If no name is defined, the class name is given.

    Attributes
    ----------
    axis : :class:`compas.geometry.Line`
        Line axis of the beam.
    section : :class:`compas.geometry.Polygon`
        Section polygon of a beam.
    polygon_bottom : :class:`compas.geometry.Polygon`
        The bottom polygon of the column.
    polygon_top : :class:`compas.geometry.Polygon`
        The top polygon of the column.
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.

    """

    @property
    def __data__(self) -> dict[str, any]:
        data: dict[str, any] = super(ColumnSquareElement, self).__data__

        data["width"] = self.width
        data["depth"] = self.depth
        data["height"] = self.height
        data["frame_top"] = self.frame_top

        return data

    @classmethod
    def __from_data__(cls, data: dict[str, any]) -> "ColumnSquareElement":
        return cls(
            width=data["width"],
            depth=data["depth"],
            height=data["height"],
            frame_bottom=data["frame"],
            frame_top=data["frame_top"],
            name=data["name"],
        )

    def __init__(
        self,
        width: float = 0.4,
        depth: float = 0.4,
        height: float = 3.0,
        frame_bottom: Plane = Frame.worldXY(),
        frame_top: Plane = None,
        name: str = "None",
    ) -> "ColumnSquareElement":
        super(ColumnSquareElement, self).__init__(frame=frame_bottom, name=name)

        self.width = width
        self.depth = depth
        self.height = height
        self.frame_bottom = frame_bottom
        self.axis: Line = Line([0, 0, 0], [0, 0, height])
        p3: list[float] = [-width * 0.5, -depth * 0.5, 0]
        p2: list[float] = [-width * 0.5, depth * 0.5, 0]
        p1: list[float] = [width * 0.5, depth * 0.5, 0]
        p0: list[float] = [width * 0.5, -depth * 0.5, 0]
        self.section: Polygon = Polygon([p0, p1, p2, p3])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()
        self.shape: Mesh = self.compute_shape()

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

    def compute_shape(self) -> Mesh:
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
    # Constructors - DO NOT MAKE ANY OVERLOAD CONSTRUCTORS - Stay Simple!
    # =============================================================================

    def rebuild(self, height: float) -> "ColumnSquareElement":
        """Rebuild the column with a new height.

        Parameters
        ----------
        height : float
            The new height of the column.

        Returns
        -------
        :class:`ColumnSquareElement`
            The new column element.
        """
        return ColumnSquareElement(width=self.width, depth=self.depth, height=height)
