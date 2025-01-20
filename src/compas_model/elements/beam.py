from typing import Optional
from typing import Type

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import Translation
from compas.geometry import intersection_line_plane
from compas.geometry import is_point_in_polygon_xy
from compas_model.elements.element import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Modifier
from compas_model.interactions import SlicerModifier


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
    center_line : :class:`compas.geometry.Line`
        Line axis of the beam.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "depth": self.depth,
            "length": self.length,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.1,
        depth: float = 0.2,
        length: float = 3.0,
        transformation: Optional[Transformation] = None,
        features: Optional[list[BeamFeature]] = None,
        name: Optional[str] = None,
    ) -> "BeamElement":
        super().__init__(transformation=transformation, features=features, name=name)

        self.width: float = width
        self.depth: float = depth
        self._length: float = length

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the beam from the given polygons .
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        box: Box = Box.from_width_height_depth(self.width, self.length, self.depth)
        box.translate([0, 0, self.length * 0.5])
        return box.to_mesh()

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, length: float):
        self._length = length
        self.compute_elementgeometry()

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.length])

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
        box = self.modelgeometry.aabb
        if self.inflate_aabb and self.inflate_aabb != 1.0:
            box.xsize += self.inflate_aabb
            box.ysize += self.inflate_aabb
            box.zsize += self.inflate_aabb
        self._aabb = box
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
        box = self.modelgeometry.obb
        if self.inflate_aabb and self.inflate_aabb != 1.0:
            box.xsize += self.inflate_obb
            box.ysize += self.inflate_obb
            box.zsize += self.inflate_obb
        self._obb = box
        return box

    def compute_collision_mesh(self) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision mesh.
        """
        mesh = self.modelgeometry.convex_hull
        self._collision_mesh = mesh
        return mesh

    def compute_point(self) -> Point:
        return Point(*self.modelgeometry.centroid())

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

    def _add_modifier_with_beam(self, target_element: "BeamElement", modifier_type: Type[Modifier] = None, **kwargs) -> Modifier:
        if not modifier_type:
            raise ValueError("Modifier type is not defined, please define a modifier type e.g. SlicerModfier.")

        if issubclass(modifier_type, BooleanModifier):
            return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))

        if issubclass(modifier_type, SlicerModifier):
            return self._create_slicer_modifier(target_element)

        raise ValueError(f"Unknown modifier type: {modifier_type}")

    def _create_slicer_modifier(self, target_element: "BeamElement") -> Modifier:
        mesh = self.elementgeometry.transformed(self.modeltransformation)
        center_line = target_element.center_line.transformed(target_element.modeltransformation)

        p0 = center_line.start
        p1 = center_line.end

        closest_distance_to_end_point = float("inf")
        closest_face = 0
        for face in self.elementgeometry.faces():
            polygon = mesh.face_polygon(face)
            frame = polygon.frame
            result = intersection_line_plane(center_line, Plane.from_frame(frame))
            if result:
                point = Point(*result)
                xform = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                point = point.transformed(xform)
                polygon = polygon.transformed(xform)
                if is_point_in_polygon_xy(point, polygon):
                    d = max(p0.distance_to_point(point), p1.distance_to_point(point))
                    if d < closest_distance_to_end_point:
                        closest_distance_to_end_point = d
                        closest_face = face

        plane = Plane.from_frame(mesh.face_polygon(closest_face).frame)
        plane = Plane(plane.point, -plane.normal)
        return SlicerModifier(plane)
