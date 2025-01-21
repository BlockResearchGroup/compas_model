from typing import Optional
from typing import Type

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
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
    """Class representing a beam element with a square section, constructed from the WorldXY Frame.
    The column is defined in its local frame, where the height corresponds to the Z-Axis, the depth to the Y-Axis, and the width to the X-Axis.
    By default, the local frame is set to WorldXY frame.

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
            "width": self.box.xsize,
            "depth": self.box.ysize,
            "height": self.box.zsize,
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
        self._box = Box.from_width_height_depth(width, height, depth)
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
    def height(self) -> float:
        return self.box.zsize

    @height.setter
    def height(self, height: float):
        self.box.zsize = height
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.box.height])

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================
    def compute_elementgeometry(self) -> Mesh:
        """Compute the mesh shape from a box.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
        """
        return self._box.to_mesh()

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance : float
            The distance to extend the beam.
        """

        self._box.zsize = self.length + distance * 2
        self._box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

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
        box = self._box.transformed(self.modeltransformation)
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
        # This method applies the boolean modifier for the pair of column and a beam.
        return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))
