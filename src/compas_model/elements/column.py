from typing import Optional
from typing import Type

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Transformation
from compas_model.elements import BeamElement
from compas_model.elements import Element
from compas_model.elements.element import Feature
from compas_model.interactions import BooleanModifier
from compas_model.interactions import Modifier


class ColumnFeature(Feature):
    pass


class ColumnElement(Element):
    """Class representing a column element with a square section, constructed from WorldXY Frame.
    Column is defined on WorldXY frame. Width is equal to X-Axis, depth is equal to Y-Axis, height is equal to Z-Axis.

    Parameters
    ----------
    width : float
        The width of the column.
    depth : float
        The depth of the column.
    height : float
        The height of the column.
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
    center_line : :class:`compas.geometry.Line`
        Line axis of the column.
    """

    @property
    def __data__(self) -> dict:
        return {
            "width": self.width,
            "depth": self.depth,
            "height": self.height,
            "transformation": self.transformation,
            "features": self._features,
            "name": self.name,
        }

    def __init__(
        self,
        width: float = 0.4,
        depth: float = 0.4,
        height: float = 3.0,
        transformation: Optional[Transformation] = None,
        features: Optional[list[ColumnFeature]] = None,
        name: Optional[str] = None,
    ) -> "ColumnElement":
        super().__init__(transformation=transformation, features=features, name=name)
        self.width = width
        self.depth = depth
        self._height = height

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, height: float):
        self._height = height

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.length])

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
        return self.modelgeometry

    def compute_point(self) -> Point:
        return Point(*self.modelgeometry.centroid())

    def compute_elementgeometry(self) -> Mesh:
        """Compute the shape of the beam from the given polygons .
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        box: Box = Box.from_width_height_depth(self.width, self.height, self.depth)
        box.translate([0, 0, self.height * 0.5])
        return box.to_mesh()

    def _add_modifier_with_beam(self, target_element: "BeamElement", modifier_type: Type[Modifier] = None, **kwargs) -> Modifier:
        return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))
