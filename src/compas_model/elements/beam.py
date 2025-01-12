from typing import TYPE_CHECKING
from typing import Optional
from typing import Union

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
from compas.geometry import intersection_line_plane
from compas.geometry import mirror_points_line
from compas.geometry import oriented_bounding_box
from compas.itertools import pairwise
from compas_model.elements.element import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier

if TYPE_CHECKING:
    from compas_model.elements import BlockElement


class BeamFeature(Feature):
    pass


class BeamElement(Element):
    """Class representing a beam element."""

    pass


class BeamSquareElement(BeamElement):
    """Class representing a beam element with a square section.

    Parameters
    ----------
    width : float
        The width of the beam.
    depth : float
        The depth of the beam.
    length : float
        The length of the beam.
    frame_bottom : :class:`compas.geometry.Frame`
        Main frame of the beam.
    frame_top : :class:`compas.geometry.Frame`
        Second frame of the beam that is used to cut the second end, while the first frame is used to cut the first end.
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
        length: float = 3.0,
        frame_top: Optional[Plane] = None,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamSquareElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = width
        self.depth: float = depth
        self._length: float = length

        self.points: list[list[float]] = [[-width * 1, -depth * 0.5, 0], [-width * 1, depth * 0.5, 0], [width * 0, depth * 0.5, 0], [width * 0, -depth * 0.5, 0]]

        self.section: Polygon = Polygon(self.points).translated([0, 0, 0.5 * length])
        self.axis: Line = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
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


class BeamIProfileElement(BeamElement):
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
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamIProfileElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = width
        self.depth: float = depth
        self.thickness: float = thickness
        self._length: float = length

        self.points: list[float] = [
            [0, -self.depth * 0.5, 0],
            [0, self.depth * 0.5, 0],
            [-self.thickness, self.depth * 0.5, 0],
            [-self.thickness, self.thickness * 0.5, 0],
            [-self.width + self.thickness, self.thickness * 0.5, 0],
            [-self.width + self.thickness, self.depth * 0.5, 0],
            [-self.width, self.depth * 0.5, 0],
            [-self.width, -self.depth * 0.5, 0],
            [-self.width + self.thickness, -self.depth * 0.5, 0],
            [-self.width + self.thickness, -self.thickness * 0.5, 0],
            [-self.thickness, -self.thickness * 0.5, 0],
            [-self.thickness, -self.depth * 0.5, 0],
        ]

        # Create the polygon of the I profile
        self.section: Polygon = Polygon(list(self.points)).translated([0, 0, 0.5 * length])

        self.axis: Line = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
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

        from compas.geometry import earclip_polygon

        offset: int = len(self.polygon_bottom)
        vertices: list[Point] = self.polygon_bottom.points + self.polygon_top.points  # type: ignore

        triangles: list[list[int]] = earclip_polygon(Polygon(self.polygon_bottom.points))
        top_faces: list[list[int]] = []
        bottom_faces: list[list[int]] = []
        for i in range(len(triangles)):
            triangle_top: list[int] = []
            triangle_bottom: list[int] = []
            for j in range(3):
                triangle_top.append(triangles[i][j] + offset)
                triangle_bottom.append(triangles[i][j])
            triangle_bottom.reverse()
            top_faces.append(triangle_top)
            bottom_faces.append(triangle_bottom)
        faces: list[list[int]] = bottom_faces + top_faces

        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([c, d, b, a])
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
    # ============================================================================


class BeamTProfileElement(BeamElement):
    """Class representing a beam element with I profile.

    Parameters
    ----------
    width : float, optional
        The width of the beam.
    height : float, optional
        The height of the beam.
    step_width_left : float, optional
        The step width on the left side of the beam.
    step_height_left : float, optional
        The step height on the left side of the beam.
    length : float, optional
        The length of the beam.
    inverted : bool, optional
        Flag indicating if the beam section is inverted as upside down letter T.
    step_width_right : float, optional
        The step width on the right side of the beam, if None then the left side step width is used.
    step_height_right : float, optional
        The step height on the right side of the beam, if None then the left side step height is used.
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
            "height": self.height,
            "step_width_left": self.step_width_left,
            "step_height_left": self.step_height_left,
            "length": self.length,
            "inverted": self.inverted,
            "step_height_right": self.step_height_right,
            "step_width_right": self.step_width_right,
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
        height: float = 0.2,
        step_width_left: float = 0.02,
        step_height_left: float = 0.02,
        length: float = 3.0,
        inverted: bool = False,
        step_height_right: Optional[float] = None,
        step_width_right: Optional[float] = None,
        frame_top: Optional[Plane] = None,
        is_support: bool = False,
        frame: Frame = Frame.worldXY(),
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamIProfileElement":
        super().__init__(frame=frame, transformation=transformation, features=features, name=name)

        self.is_support: bool = is_support

        self.width: float = abs(width)
        self.height: float = abs(height)
        self.step_width_left: float = abs(step_width_left)
        self.step_width_right: float = abs(step_width_right) if step_width_right is not None else step_width_left
        self.step_height_left: float = abs(step_height_left)
        self.step_height_right: float = abs(step_height_right) if step_height_right is not None else step_height_left
        self.inverted: bool = inverted
        self._length: float = abs(length)

        self.step_width_left = min(self.step_width_left, width * 0.5 * 0.999)
        self.step_width_right = min(self.step_width_right, width * 0.5 * 0.999)
        self.step_height_left = min(self.step_height_left, height)
        self.step_height_right = min(self.step_height_right, height)

        self.points: list[float] = [
            [self.width * 0.5, -self.height * 0.5, 0],
            [-self.width * 0.5, -self.height * 0.5, 0],
            [-self.width * 0.5, -self.height * 0.5 + self.step_height_left, 0],
            [-self.width * 0.5 + self.step_width_left, -self.height * 0.5 + self.step_height_left, 0],
            [-self.width * 0.5 + self.step_width_left, self.height * 0.5, 0],
            [self.width * 0.5 - self.step_width_right, self.height * 0.5, 0],
            [self.width * 0.5 - self.step_width_right, -self.height * 0.5 + self.step_height_right, 0],
            [self.width * 0.5, -self.height * 0.5 + self.step_height_right, 0],
        ]

        if inverted:
            mirror_line: Line = Line([0, 0, 0], [1, 0, 0])
            self.points = mirror_points_line(self.points, mirror_line)

        # Create the polygon of the T profile
        self.section: Polygon = Polygon(list(self.points)).translated([0, 0, 0.5 * length])

        self.axis: Line = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top: Frame = frame_top or Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
        self.polygon_bottom, self.polygon_top = self.compute_top_and_bottom_polygons()

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length

        self.section = Polygon(list(self.points)).translated([0, 0, 0.5 * length])

        self.axis = Line([0, 0, 0], [0, 0, length]).translated([0, 0, 0.5 * length])
        self.frame_top = Frame(self.frame.point + self.axis.vector, self.frame.xaxis, self.frame.yaxis)
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

        from compas.geometry import earclip_polygon

        offset: int = len(self.polygon_bottom)
        vertices: list[Point] = self.polygon_bottom.points + self.polygon_top.points  # type: ignore

        triangles: list[list[int]] = earclip_polygon(Polygon(self.polygon_bottom.points))
        top_faces: list[list[int]] = []
        bottom_faces: list[list[int]] = []
        for i in range(len(triangles)):
            triangle_top: list[int] = []
            triangle_bottom: list[int] = []
            for j in range(3):
                triangle_top.append(triangles[i][j] + offset)
                triangle_bottom.append(triangles[i][j])
            triangle_bottom.reverse()
            top_faces.append(triangle_top)
            bottom_faces.append(triangle_bottom)
        faces: list[list[int]] = bottom_faces + top_faces

        bottom: list[int] = list(range(offset))
        top: list[int] = [i + offset for i in bottom]
        for (a, b), (c, d) in zip(pairwise(bottom + bottom[:1]), pairwise(top + top[:1])):
            faces.append([c, d, b, a])
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

    def compute_contact(self, target_element: Element, type: str = "") -> BooleanModifier:
        """Computes the contact interaction of the geometry of the elements that is used in the model's add_contact method.

        Returns
        -------
        :class:`compas_model.interactions.BooleanModifier`
            The ContactInteraction that is applied to the neighboring element. One pair can have one or multiple variants.
        target_element : Element
            The target element to compute the contact interaction.
        type : str, optional
            The type of contact interaction, if different contact are possible between the two elements.

        """
        # Traverse up to the class one before the Element class.add()
        # Create a function name based on the target_element class name.
        parent_class = target_element.__class__
        while parent_class.__bases__[0] != Element:
            parent_class = parent_class.__bases__[0]

        parent_class_name = parent_class.__name__.lower().replace("element", "")
        method_name = f"_compute_contact_with_{parent_class_name}"
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Unsupported target element type: {type(target_element)}")

        return method(target_element, type)

    def _compute_contact_with_block(self, target_element: "BlockElement", type: str) -> Union["BooleanModifier", None]:
        # Scenario:
        # A beam with a profile applies boolean difference with a block geometry.
        if target_element.is_support:
            return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))
        else:
            return None

    # =============================================================================
    # Constructors
    # =============================================================================
