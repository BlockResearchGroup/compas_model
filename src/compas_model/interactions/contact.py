from typing import Optional

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bestfit_frame_numpy

# only required param should be `points`, as in "contact points"
# everything else can be computed from those points if needed
# when additional information is already available it can of course be included


class Contact(Data):
    """Class representing a planar contact between two elements.

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        The points defining the contact polygon.
    frame : :class:`compas.geometry.Frame`
        The local coordinate system of the contact.
    size : float
        The total area of the contact polygon.
    mesh : :class:`compas.datastructures.Mesh`, optional
        The mesh representation of the contact surface.
    name : str, optional
        A human-readable name.

    Attributes
    ----------
    frame : :class:`compas.geometry.Frame`
        The local coordinate frame of the interface polygon.
    mesh : :class:`compas.datastructure.Mesh`
        A mesh representation of the interface.
    points : list[:class:`compas.geometry.Point`]
        The corner points of the interface polygon.
    polygon : :class:`compas.geometry.Polygon`
        The interfaces polygon.
    size : float
        The area of the interface polygon.

    Warnings
    --------
    The definition of contact surfaces is under active development and may change frequently.

    """

    @property
    def __data__(self) -> dict:
        return {
            "points": self.points,
            "frame": self._frame,
            "size": self._size,
            "mesh": self._mesh,
            "name": self.name,
        }

    def __init__(
        self,
        points: list[Point],
        frame: Optional[Frame] = None,
        size: Optional[float] = None,
        mesh: Optional[Mesh] = None,
        name: Optional[str] = None,
    ):
        super().__init__(name)

        self._frame = frame
        self._size = size
        self._mesh = mesh
        self._polygon = Polygon(points)

    @property
    def polygon(self) -> Polygon:
        return self._polygon

    @property
    def geometry(self):
        return self.polygon

    @property
    def points(self) -> list[Point]:
        return self.polygon.points

    @property
    def frame(self) -> Frame:
        if self._frame is None:
            self._frame = Frame(*bestfit_frame_numpy(self.points))
            if self._frame.zaxis.dot(self.polygon.normal) < 0:
                self._frame.invert()
        return self._frame

    @property
    def mesh(self) -> Mesh:
        if self._mesh is None:
            self._mesh = Mesh.from_polygons([self.polygon])
        return self._mesh

    @property
    def size(self):
        if self._size is None:
            self._size = self.polygon.area
        return self._size
