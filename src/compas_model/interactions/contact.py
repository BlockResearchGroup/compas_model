from typing import Optional
from typing import Union

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import bestfit_frame_numpy


class Contact(Data):
    """Class representing a planar contact between two elements.

    Parameters
    ----------
    points
    frame
    size
    forces
    mesh
    name

    Attributes
    ----------
    points : list[:class:`compas.geometry.Point`]
        The corner points of the interface polygon.
    size : float
        The area of the interface polygon.
    frame : :class:`Frame`
        The local coordinate frame of the interface polygon.
    polygon : :class:`compas.geometry.Polygon`
        The polygon defining the contact interface.
    mesh : :class:`Mesh`
        A mesh representation of the interface.

    """

    @property
    def __data__(self) -> dict:
        return {
            "points": self.points,
            "size": self.size,
            "frame": self.frame,
            "mesh": self.mesh,
            "name": self.name,
        }

    def __init__(
        self,
        points: Optional[list[Point]] = None,
        frame: Optional[Frame] = None,
        size: Optional[float] = None,
        mesh: Optional[Mesh] = None,
        name: Optional[str] = None,
    ):
        super().__init__(name)

        self._mesh = None
        self._size = None
        self._points = None
        self._polygon = None
        self._frame = frame

        self.points = points
        self.mesh = mesh
        self.size = size

    @property
    def geometry(self):
        return self.polygon

    @property
    def points(self) -> Union[list[Point], None]:
        return self._points

    @points.setter
    def points(self, items: Union[list[Point], list[list[float]]]) -> None:
        self._points = []
        for item in items:
            self._points.append(Point(*item))

    @property
    def polygon(self) -> Polygon:
        if self._polygon is None:
            self._polygon = Polygon(self.points)
        return self._polygon

    @property
    def frame(self) -> Frame:
        if self._frame is None:
            self._frame = Frame(*bestfit_frame_numpy(self.points))
            if self._frame.zaxis.dot(self.polygon.normal) < 0:
                self._frame.invert()
        return self._frame

    @property
    def mesh(self) -> Mesh:
        if not self._mesh:
            self._mesh = Mesh.from_polygons([self.polygon])
        return self._mesh

    @mesh.setter
    def mesh(self, mesh: Mesh) -> None:
        self._mesh = mesh
