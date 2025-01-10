from typing import Annotated
from typing import Optional
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import centroid_points_weighted
from compas.geometry import dot_vectors
from compas.geometry import transform_points
from compas.itertools import pairwise

from .interaction import Interaction


def outer_product(u, v):
    return [[ui * vi for vi in v] for ui in u]


def scale_matrix(M, scale):
    r = len(M)
    c = len(M[0])
    for i in range(r):
        for j in range(c):
            M[i][j] *= scale
    return M


def sum_matrices(A, B):
    r = len(A)
    c = len(A[0])
    M = [[None for j in range(c)] for i in range(r)]
    for i in range(r):
        for j in range(c):
            M[i][j] = A[i][j] + B[i][j]
    return M


class ContactInterface(Interaction):
    """Class representing an interaction between two elements through surface-to-surface contact.

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
    points : list[:class:`Point`]
        The corner points of the interface polygon.
    size : float
        The area of the interface polygon.
    frame : :class:`Frame`
        The local coordinate frame of the interface polygon.
    polygon : :class:`Polygon`
        The polygon defining the contact interface.
    mesh : :class:`Mesh`
        A mesh representation of the interface.
    kern : :class:`Polygon`
        The "kern" part of the interface polygon.
    forces : list[dict]
        A dictionary of force components per interface point.
        Each dictionary contains the following items: ``{"c_np": ..., "c_nn": ...,  "c_u": ..., "c_v": ...}``.
    stressdistribution : ???
        ???
    normalforces : list[:class:`Line`]
        A list of lines representing the normal components of the contact forces at the corners of the interface.
        The length of each line is proportional to the magnitude of the corresponding force.
    compressionforces : list[:class:`Line`]
        A list of lines representing the compression components of the normal contact forces
        at the corners of the interface.
        The length of each line is proportional to the magnitude of the corresponding force.
    tensionforces : list[:class:`Line`]
        A list of lines representing the tension components of the normal contact forces
        at the corners of the interface.
        The length of each line is proportional to the magnitude of the corresponding force.
    frictionforces : list[:class:`Line`]
        A list of lines representing the friction or tangential components of the contact forces
        at the corners of the interface.
        The length of each line is proportional to the magnitude of the corresponding force.
    resultantforce : list[:class:`Line`]
        A list with a single line representing the resultant of all the contact forces at the corners of the interface.
        The length of the line is proportional to the magnitude of the resultant force.
    resultantpoint : :class:`Point`
        The point of application of the resultant force on the interface.

    """

    @property
    def __data__(self) -> dict:
        return {
            "points": self.points,
            "size": self.size,
            "frame": self.frame,
            "forces": self.forces,
            "mesh": self.mesh,
            "name": self.name,
        }

    def __init__(
        self,
        points: Optional[list[Point]] = None,
        frame: Optional[Frame] = None,
        size: Optional[float] = None,
        forces: Optional[list[float]] = None,
        mesh: Optional[Mesh] = None,
        name: Optional[str] = None,
    ):
        super().__init__(name)

        self._mesh = None
        self._size = None
        self._points = None
        self._polygon = None
        self._points2 = None
        self._polygon2 = None

        self.points = points
        self.mesh = mesh
        self.size = size
        self.forces = forces

        self._frame = frame

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
            from compas.geometry import bestfit_frame_numpy

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

    @property
    def points2(self) -> list[Point]:
        if not self._points2:
            X = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
            self._points2 = [Point(*point) for point in transform_points(self.points, X)]
        return self._points2

    @property
    def polygon2(self) -> Polygon:
        if not self._polygon2:
            X = Transformation.from_frame_to_frame(self.frame, Frame.worldXY())
            self._polygon2 = self.polygon.transformed(X)
        return self._polygon2

    @property
    def M0(self) -> float:
        m0 = 0
        for a, b in pairwise(self.points2 + self.points2[:1]):
            d = b - a
            n = [d[1], -d[0], 0]
            m0 += dot_vectors(a, n)
        return 0.5 * m0

    @property
    def M1(self) -> Point:
        m1 = Point(0, 0, 0)
        for a, b in pairwise(self.points2 + self.points2[:1]):
            d = b - a
            n = [d[1], -d[0], 0]
            m0 = dot_vectors(a, n)
            m1 += (a + b) * m0
        return m1 / 6

    @property
    def M2(self) -> Annotated[list[Annotated[list[float], 3]], 3]:
        m2 = outer_product([0, 0, 0], [0, 0, 0])
        for a, b in pairwise(self.points2 + self.points2[:1]):
            d = b - a
            n = [d[1], -d[0], 0]
            m0 = dot_vectors(a, n)
            aa = outer_product(a, a)
            ab = outer_product(a, b)
            ba = outer_product(b, a)
            bb = outer_product(b, b)
            m2 = sum_matrices(
                m2,
                scale_matrix(
                    sum_matrices(sum_matrices(aa, bb), scale_matrix(sum_matrices(ab, ba), 0.5)),
                    m0,
                ),
            )
        return scale_matrix(m2, 1 / 12.0)

    @property
    def kern(self):
        raise NotImplementedError

    @property
    def stressdistribution(self):
        raise NotImplementedError

    @property
    def normalforces(self) -> list[Line]:
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            force = force["c_np"] - force["c_nn"]
            p1 = point + w * force * 0.5
            p2 = point - w * force * 0.5
            lines.append(Line(p1, p2))
        return lines

    @property
    def compressionforces(self) -> list[Line]:
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            force = force["c_np"] - force["c_nn"]
            if force > 0:
                p1 = point + w * force * 0.5
                p2 = point - w * force * 0.5
                lines.append(Line(p1, p2))
        return lines

    @property
    def tensionforces(self) -> list[Line]:
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            force = force["c_np"] - force["c_nn"]
            if force < 0:
                p1 = point + w * force * 0.5
                p2 = point - w * force * 0.5
                lines.append(Line(p1, p2))
        return lines

    @property
    def frictionforces(self) -> list[Line]:
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        u, v = frame.xaxis, frame.yaxis
        for point, force in zip(self.points, self.forces):
            ft_uv = (u * force["c_u"] + v * force["c_v"]) * 0.5
            p1 = point + ft_uv
            p2 = point - ft_uv
            lines.append(Line(p1, p2))
        return lines

    @property
    def resultantpoint(self) -> list[float]:
        if not self.forces:
            return []
        normalcomponents = [f["c_np"] - f["c_nn"] for f in self.forces]
        if sum(normalcomponents):
            return Point(*centroid_points_weighted(self.points, normalcomponents))

    @property
    def resultantforce(self) -> list[Line]:
        if not self.forces:
            return []
        normalcomponents = [f["c_np"] - f["c_nn"] for f in self.forces]
        sum_n = sum(normalcomponents)
        sum_u = sum(f["c_u"] for f in self.forces)
        sum_v = sum(f["c_v"] for f in self.forces)
        position = Point(*centroid_points_weighted(self.points, normalcomponents))
        frame = self.frame
        w, u, v = frame.zaxis, frame.xaxis, frame.yaxis
        forcevector = (w * sum_n + u * sum_u + v * sum_v) * 0.5
        p1 = position + forcevector
        p2 = position - forcevector
        return [Line(p1, p2)]

    def apply(self, targetgeometry: Union[Brep, Mesh]):
        """Cut target geometry by the frame.

        Parameters
        ----------
        targetgeometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        """
        # Local import is needed otherwise, remove contact interactions in algorithms module.
        from compas_model.algorithms.modifiers import slice

        return slice(targetgeometry, Plane.from_frame(self.frame))
