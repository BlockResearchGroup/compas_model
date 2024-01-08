from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import Point
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import Frame
from compas.geometry import cross_vectors
from compas_model.elements.triangulator import Triagulator

from compas_model.elements.element import Element
from collections import OrderedDict

from compas_model.model import Model


class Interface(Element):
    """
    A data structure for representing interfaces between blocks
    and managing their geometrical and structural properties.

    The implementation is inspired by the compas_assembly interface class:
    https://github.com/BlockResearchGroup/compas_assembly/blob/main/src/compas_assembly/datastructures/interface.py

    Parameters
    ----------
    points : list[:class:`compas.geometry.Point`]
        The points defining the interface polygon.
    mesh : :class:`compas.datastructures.Mesh`
        The mesh representing the interface.
    interaction : tuple(:class:`compas_model.elements.Element`)
        The pair of elements on either side of the interface.
    model : :class:`compas_model.model.Model`
        The model the interface belongs to.

    Attributes
    ----------
    model : :class:`compas_model.model.Model`
        The model the interface belongs to, this value is not serialized and must be assigned.
    size : float
        The area of the interface.
    interaction : ``tuple(str(guid), str(guid))``
        The pair of element identifiers on either side of the interface.
    forces : list[:class:`compas.geometry.Vector`]
        The forces acting on the interface.
    name : str
        Name of the element.
    frame : :class:`compas.geometry.Frame`
        Local coordinate of the object.
    geometry_simplified : Any
        Minimal geometrical represetation of an object. For example a :class:`compas.geometry.Polyline` that can represent: a point, a line or a polyline.
    geometry : Any
        A list of closed shapes. For example a box of a beam, a mesh of a block and etc.
    id : int
        Index of the object, default is -1.
    key : str
        Guid of the class object as a string.
    insertion : :class:`compas.geometry.Vector`
        Direction of the element.
    aabb : :class:`compas.geometry.Box`:
        Axis-aligned-bounding-box.
    oobb : :class:`compas.geometry.Box`:
        Object-oriented-bounding-box.
    center : :class:`compas.geometry.Point`
        The center of the element. Currently the center is computed from the axis-aligned-bounding-box.
    area : float
        The area of the geometry. Measurement is made from the ``geometry``.
    volume : float
        The volume of the geometry. Measurement is made from the ``geometry``.
    center_of_mass : :class:`compas.geometry.Point`
        The center of mass of the geometry. Measurement is made from the ``geometry``.
    centroid : :class:`compas.geometry.Point`
        The centroid of the geometry. Measurement is made from the ``geometry``.
    is_support : bool
        Indicates whether the element is a support.
    display_schema : dict
        Information which attributes are visible in the viewer and how they are visualized.

    """

    def __init__(self, polygon, interaction=None, model=None, **kwargs):
        # --------------------------------------------------------------------------
        # Create frame from points
        # --------------------------------------------------------------------------
        frame = self._get_average_plane(polygon)

        # --------------------------------------------------------------------------
        # Create mesh
        # --------------------------------------------------------------------------
        mesh = Triagulator.from_points(polygon.points)

        # --------------------------------------------------------------------------
        # Call the Element constructor
        # --------------------------------------------------------------------------
        super(Interface, self).__init__(
            name=str.lower(self.__class__.__name__),
            frame=frame,
            geometry_simplified=[polygon],
            geometry=[mesh],
            copy_geometry=True,
            **kwargs
        )

        # --------------------------------------------------------------------------
        # Attributes related to model, currently the model is not stored here
        # --------------------------------------------------------------------------
        if interaction and model:
            self._model = model
            self._interaction = model.add_interaction(interaction[0], interaction[1])

        # --------------------------------------------------------------------------
        # Attributes specific to this class
        # --------------------------------------------------------------------------
        self._size = self.geometry_simplified[0].area
        self._forces = []
        self._interaction = None
        self._model = None

    # ==========================================================================
    # Serialization
    # ==========================================================================

    @property
    def data(self):
        data = {
            "name": self.name,
            "frame": self.frame,
            "geometry_simplified": self.geometry_simplified,
            "geometry": self.geometry,
            "is_support": self.is_support,
            # "attributes": self.attributes,
        }

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        data["id"] = self.id
        data["insertion"] = self.insertion

        # The display schema can be replaced in the future by scene configuration file.
        data["display_schema"] = self.display_schema
        data["forces"] = self.forces
        data["interaction"] = self.interaction
        data["size"] = self.size

        return data

    @classmethod
    def from_data(cls, data):
        obj = cls(
            polygon=data["geometry_simplified"][0],
            interaction=data["interaction"],
            # **data["attributes"],
        )

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.is_support = data["is_support"]

        # The display schema can be replaced in the future by scene configuration file.
        obj._display_schema = OrderedDict(data["display_schema"].items())
        obj.size = data["size"]

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def model(self):
        self._model

    @model.setter
    def model(self, value):
        if isinstance(value, Model):
            self._model = value
        else:
            raise TypeError("The value is not of type Model.")

    @property
    def interaction(self):
        self._interaction

    @interaction.setter
    def interaction(self, value):
        if (
            isinstance(value, tuple)
            and len(value) == 2
            and all(isinstance(x, str) for x in value)
        ):
            self._interaction = value
        else:
            raise TypeError("Interaction is not of type tuple(str, str).")

    @property
    def polygon(self):
        return Polygon(self.geometry_simplified[0])

    @property
    def points(self):
        return self.polygon.points

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        if isinstance(value, float):
            self._size = value
        else:
            raise TypeError("The value is not of type float.")

    @property
    def forces(self):
        return self._forces

    @forces.setter
    def forces(self, value):
        if isinstance(value, list):
            self._forces = value
        else:
            raise TypeError("The value is not of type list.")

    @property
    def display_schema(self):
        face_color = [0.9, 0.9, 0.9] if not self.is_support else [0.968, 0.615, 0.517]

        values = OrderedDict(
            [
                ("geometry_simplified", {"is_visible": True}),
                (
                    "geometry",
                    {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                ),
                ("frame", {}),
                ("aabb", {"opacity": 0.25}),
                ("oobb", {"opacity": 0.25}),
            ]
        )

        # --------------------------------------------------------------------------
        # create forces display schema
        # --------------------------------------------------------------------------
        if hasattr(self, "_forces"):
            for force_tuple in self._forces:
                setattr(self, force_tuple[0], force_tuple[1])
                values[force_tuple[0]] = {
                    "is_visible": True,
                    "facecolor": force_tuple[2],
                    "linewidth": 0.0001,
                }

        return values

    # ==========================================================================
    # Methods
    # ==========================================================================
    def add_forces(self, name, points=[], vectors=[], thickness=10, color=[0, 0, 0]):
        """Add forces for the vizualization."""

        # --------------------------------------------------------------------------
        # Add lines as attribute.
        # --------------------------------------------------------------------------
        lines = []
        for point, vector in zip(points, vectors):
            if vector.length < 1e-3:
                continue
            line = Line(point, point + vector)
            lines.append(line)

        self.forces.append((name, lines, color))

    # ==========================================================================
    # Private geometry methods
    # ==========================================================================

    def _get_average_plane(self, polygon):
        # --------------------------------------------------------------------------
        # number of points
        # --------------------------------------------------------------------------
        n = len(polygon.points)

        # --------------------------------------------------------------------------
        # origin
        # --------------------------------------------------------------------------
        origin = Point(0, 0, 0)
        for point in polygon.points:
            origin = origin + point
        origin = origin / n

        # --------------------------------------------------------------------------
        # xaxis
        # --------------------------------------------------------------------------
        xaxis = polygon.points[1] - polygon.points[0]
        xaxis.unitize()

        # --------------------------------------------------------------------------
        # zaxis
        # --------------------------------------------------------------------------
        zaxis = Vector(0, 0, 0)

        for i in range(n):
            prev_id = ((i - 1) + n) % n
            next_id = ((i + 1) + n) % n
            zaxis = zaxis + cross_vectors(
                polygon.points[i] - polygon.points[prev_id],
                polygon.points[next_id] - polygon.points[i],
            )

        zaxis.unitize()

        # --------------------------------------------------------------------------
        # yaxis
        # --------------------------------------------------------------------------
        yaxis = cross_vectors(zaxis, xaxis)

        # --------------------------------------------------------------------------
        # frame
        # --------------------------------------------------------------------------
        frame = Frame(origin, xaxis, yaxis)

        return frame
