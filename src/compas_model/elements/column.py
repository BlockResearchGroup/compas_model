from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Transformation
from compas_model.elements import Element
from compas_model.elements.element import Feature

# from compas_model.interactions import BooleanModifier
# from compas_model.interactions import Modifier


class ColumnFeature(Feature):
    pass


class ColumnElement(Element):
    """Class representing a beam element with a square section, constructed from the WorldXY Frame.
    The column is defined in its local frame, where the height corresponds to the Z-Axis, the depth to the Y-Axis, and the width to the X-Axis.
    By default, the local frame is set to WorldXY frame.

    Parameters
    ----------
    width
        The width of the column.
    depth
        The depth of the column.
    height
        The height of the column.
    transformation
        Transformation applied to the column.
    features
        Features of the column.
    name
        If no name is defined, the class name is given.

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
    ) -> None:
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
    def width(self, width: float) -> None:
        self.box.xsize = width

    @property
    def depth(self) -> float:
        return self.box.ysize

    @depth.setter
    def depth(self, depth: float) -> None:
        self.box.ysize = depth

    @property
    def height(self) -> float:
        return self.box.zsize

    @height.setter
    def height(self, height: float) -> None:
        self.box.zsize = height
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    @property
    def center_line(self) -> Line:
        return Line([0, 0, 0], [0, 0, self.box.height])

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_elementgeometry(self, include_features: bool = False) -> Mesh:
        """Compute the mesh shape from a box.

        Returns
        -------
        Mesh
            The mesh shape.

        """
        return self.box.to_mesh()

    def extend(self, distance: float) -> None:
        """Extend the beam.

        Parameters
        ----------
        distance
            The distance to extend the beam.

        """

        self.box.zsize = self.height + distance * 2
        self.box.frame = Frame(point=[0, 0, self.box.zsize / 2], xaxis=[1, 0, 0], yaxis=[0, 1, 0])

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate
            The inflation factor of the bounding box.

        Returns
        -------
        Box
            The axis-aligned bounding box.

        """

        box = self.box.transformed(self.modeltransformation)
        box = Box.from_bounding_box(box.points)
        if inflate != 1.0:
            box.xsize *= inflate
            box.ysize *= inflate
            box.zsize *= inflate
        self._aabb = box
        return box

    def compute_obb(self, inflate: float = 1.0) -> Box:
        """Compute the oriented bounding box of the element.

        Parameters
        ----------
        inflate
            The inflation factor of the bounding box.

        Returns
        -------
        Box
            The oriented bounding box.

        """
        box = self._box.transformed(self.modeltransformation)
        if inflate != 1.0:
            box.xsize *= inflate
            box.ysize *= inflate
            box.zsize *= inflate
        self._obb = box
        return box

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        """Compute the collision mesh of the element.

        Returns
        -------
        Mesh
            The collision mesh.

        """
        raise NotImplementedError

    def compute_point(self) -> Point:
        """Compute the reference point of the column from the centroid of its geometry.

        Returns
        -------
        Point
            The reference point.

        """
        return Point(*self.modelgeometry.centroid())

    # =============================================================================
    # Modifier methods (WIP)
    # =============================================================================

    # def _add_modifier_with_beam(self, target_element: "BeamElement", modifier_type: type[Modifier] = None, **kwargs) -> Modifier:
    #     # This method applies the boolean modifier for the pair of column and a beam.
    #     return BooleanModifier(self.elementgeometry.transformed(self.modeltransformation))
