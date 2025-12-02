from typing import Optional

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Transformation
from compas_model.elements.element import Element
from compas_model.elements.element import Feature


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
    transformation : Optional[Transformation]
        Transformation applied to the beam.
    features : Optional[list[BreamFeature]]
        Features of the beam.
    name : Optional[str]
        If no name is defined, the class name is given.

    Attributes
    ----------
    box : Box
        The box geometry of the beam.
    width : float
        The width of the beam.
    depth : float
        The depth of the beam.
    length : float
        The length of the beam.
    center_line : Line
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
    ):
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

    def compute_elementgeometry(self, include_features=False) -> Mesh:
        """Compute the mesh shape from a box.

        Returns
        -------
        Mesh
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

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        """Compute the axis-aligned bounding box of the element.

        Parameters
        ----------
        inflate : float, optional
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
        inflate : float, optional
            The inflation factor of the bounding box.

        Returns
        -------
        Box
            The oriented bounding box.
        """
        box = self.box.transformed(self.modeltransformation)
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
        """Compute the reference point of the beam from the centroid of its geometry.

        Returns
        -------
        Point

        """
        return Point(*self.modelgeometry.centroid())
