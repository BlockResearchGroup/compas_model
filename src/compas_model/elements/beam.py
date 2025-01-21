from typing import Optional
from typing import Type

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Transformation
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
    """Class representing a beam element with a square section, constructed from the WorldXY Frame.
    The beam is defined in its local frame, where the length corresponds to the Z-Axis, the depth to the Y-Axis, and the width to the X-Axis.
    By default, the local frame is set to WorldXY frame.

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
    box : :class:`compas.geometry.Box`
        The box geometry of the beam.
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
            "width": self.box.xsize,
            "depth": self.box.ysize,
            "length": self.box.zsize,
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
        self._box = Box.from_width_height_depth(width, length, depth)
        self._box.frame = Frame(point=[0, 0, self._box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def box(self) -> Box:
        return self._box

    @property
    def width(self) -> float:
        return self.box.xsize

    @width.setter
    def width(self, width: float):
        self.box.xsize = width

    @property
    def depth(self) -> float:
        return self.box.ysize

    @depth.setter
    def depth(self, depth: float):
        self.box.ysize = depth

    @property
    def length(self) -> float:
        return self.box.zsize

    @length.setter
    def length(self, length: float):
        self.box.zsize = length
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.box.height])

    def compute_elementgeometry(self) -> Mesh:
        """Compute the mesh shape from a box.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        return self.box.to_mesh()

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance : float
            The distance to extend the beam.
        """

        self._box.zsize = self.length + distance * 2
        self._box.frame = Frame(point=[0, 0, self.box.zsize / 2 - distance], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

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

        box = self.box.transformed(self.modeltransformation)
        box = Box.from_bounding_box(box.points)
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
        box = self.box.transformed(self.modeltransformation)
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
        return self.modelgeometry.to_mesh()

    def compute_point(self) -> Point:
        return Point(*self.modelgeometry.centroid())

    def _add_modifier_with_beam(self, target_element: "BeamElement", modifier_type: Type[Modifier] = None, **kwargs) -> Modifier:
        #  This method constructs boolean and slicing modifiers for the pairs for beams.
        if issubclass(modifier_type, BooleanModifier):
            return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))

        if issubclass(modifier_type, SlicerModifier):
            return self._create_slicer_modifier(target_element)

        raise ValueError(f"Unsupported modifier type: {modifier_type}")

    def _create_slicer_modifier(self, target_element: "BeamElement") -> Modifier:
        # This method performs mesh-ray intersection for detecting the slicing plane.
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
