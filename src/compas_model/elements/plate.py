import compas.geometry
import compas.datastructures  # noqa: F401

from compas.geometry import convex_hull_numpy
from compas.geometry import bounding_box
from compas.geometry import oriented_bounding_box
from compas.geometry import Box
from compas.datastructures import Mesh
from compas.itertools import pairwise

from compas_model.elements import Element
from compas_model.elements import Feature


class PlateFeature(Feature):
    pass


class PlateElement(Element):
    """Class representing block elements.

    Parameters
    ----------
    shape : :class:`compas.datastructures.Mesh`
        The base shape of the block.
    features : list[:class:`PlateFeature`], optional
        Additional block features.
    is_support : bool, optional
        Flag indicating that the block is a support.
    frame : :class:`compas.geometry.Frame`, optional
        The coordinate frame of the block.
    name : str, optional
        The name of the element.

    Attributes
    ----------
    shape : :class:`compas.datastructure.Mesh`
        The base shape of the block.
    features : list[:class:`PlateFeature`]
        A list of additional block features.
    is_support : bool
        Flag indicating that the block is a support.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(PlateElement, self).__data__
        data["bottom"] = self._bottom
        data["top"] = self._top
        data["features"] = self.features
        return data

    def __init__(self, bottom, top, features=None, frame=None, name=None):
        # type: (compas.geometry.Polygon, compas.geometry.Polygon, list[PlateFeature] | None, compas.geometry.Frame | None, str | None) -> None

        super(PlateElement, self).__init__(frame=frame, name=name)
        self._bottom = bottom
        self._top = top
        self.shape = self.compute_shape()
        self.features = features or []  # type: list[PlateFeature]

    @property
    def face_polygons(self):
        # type: () -> list[compas.geometry.Polygon]
        return [self.geometry.face_polygon(face) for face in self.geometry.faces()]  # type: ignore

    def compute_shape(self):
        # type: () -> compas.datastructures.Mesh
        """Compute the shape of the plate from the given polygons and features.
        This shape is relative to the frame of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        offset = len(self._bottom)
        vertices = self._bottom + self._top  # type: ignore
        bottom = list(range(offset))
        top = [i + offset for i in bottom]
        faces = [bottom[::-1], top]
        for (a, b), (c, d) in zip(
            pairwise(bottom + bottom[:1]), pairwise(top + top[:1])
        ):
            faces.append([a, b, d, c])
        mesh = Mesh.from_vertices_and_faces(vertices, faces)
        return mesh

    # =============================================================================
    # Implementations of abstract methods
    # =============================================================================

    def compute_geometry(self, include_features=False):
        geometry = self.shape
        if include_features:
            if self.features:
                for feature in self.features:
                    geometry = feature.apply(geometry)
        geometry.transform(self.worldtransformation)
        return geometry

    def compute_aabb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_obb(self, inflate=0.0):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        box = Box.from_bounding_box(oriented_bounding_box(points))
        box.xsize += inflate
        box.ysize += inflate
        box.zsize += inflate
        return box

    def compute_collision_mesh(self):
        points = self.geometry.vertices_attributes("xyz")  # type: ignore
        vertices, faces = convex_hull_numpy(points)
        vertices = [points[index] for index in vertices]  # type: ignore
        return Mesh.from_vertices_and_faces(vertices, faces)

    # =============================================================================
    # Constructors
    # =============================================================================

    @classmethod
    def from_polygon_and_thickness(
        cls, polygon, thickness, features=None, frame=None, name=None
    ):
        # type: (compas.geometry.Polygon, float, list[PlateFeature] | None, compas.geometry.Frame | None, str | None) -> PlateElement
        """Create a plate element from a polygon and a thickness.

        Parameters
        ----------
        polygon : :class:`compas.geometry.Polygon`
            The base polygon of the plate.
        thickness : float
            The total offset thickness above and blow the polygon.

        Returns
        -------
        :class:`PlateElement`

        """
        normal = polygon.normal
        down = normal * (-0.5 * thickness)
        up = normal * (+0.5 * thickness)
        bottom = polygon.copy()
        for point in bottom.points:
            point += down
        top = polygon.copy()
        for point in top.points:
            point += up
        plate = cls(bottom, top)
        return plate
