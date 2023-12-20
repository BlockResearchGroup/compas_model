from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.geometry import Point
from compas.geometry import Line
from compas.geometry import Polygon
from compas.geometry import Vector
from compas.geometry import Frame
from compas.geometry import cross_vectors
from compas.geometry import centroid_points_weighted
from compas_model.elements.triangulator import Triagulator

from compas_model.elements.element import Element
from compas_model.elements.element import ElementType
from collections import OrderedDict
from copy import deepcopy

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
    forces : list[:class:`compas.geometry.Vector`]
        The forces acting on the interface.
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

      : list[:class:`compas.geometry.Vector`]
        The forces acting on the interface.
    contact_forces : list[:class:`compas.geometry.Line`]
        The contact forces acting on the interface.
    compression_forces : list[:class:`compas.geometry.Line`]
        The compression forces acting on the interface.
    tension_forces : list[:class:`compas.geometry.Line`]
        The tension forces acting on the interface.
    friction_forces : list[:class:`compas.geometry.Line`]
        The friction forces acting on the interface.
    resultant_force : list[:class:`compas.geometry.Line`]
        The resultant force acting on the interface.
    is_support : bool
        Indicates whether the element is a support.

    """

    def __init__(self, polygon, forces=None, interaction=None, model=None, **kwargs):

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
            name=ElementType.INTERFACE,
            frame=frame,
            geometry_simplified=[polygon],
            geometry=[mesh],
            copy_mesh=True,
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
        self.attributes = {}
        self.attributes.update(kwargs)
        self._size = self.geometry_simplified[0].area
        if forces:
            self._forces = list(forces)

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
            "attributes": self.attributes,
        }

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        data["id"] = self.id
        data["insertion"] = self.insertion
        data["frame_global"] = self.frame_global

        # The display schema can be replaced in the future by scene configuration file.
        data["display_schema"] = self.display_schema
        data["forces"] = self.forces
        data["fabrication"] = self.fabrication
        data["interaction"] = self.interaction
        data["size"] = self.size

        return data

    @classmethod
    def from_data(cls, data):

        obj = cls(
            name=data["name"],
            frame=data["frame"],
            geometry_simplified=data["geometry_simplified"],
            geometry=data["geometry"],
            **data["attributes"],
        )

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.frame_global = data["frame_global"]
        obj.is_support = data["is_support"]

        # The display schema can be replaced in the future by scene configuration file.
        obj.display_schema = OrderedDict(data["display_schema"].items())
        obj.forces = data["forces"]
        obj.fabrication = data["fabrication"]
        obj.interaction = data["interaction"]
        obj.size = data["size"]

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def model(self):
        if not hasattr(self, "_model"):
            return None
        else:
            self._model

    @model.setter
    def model(self, value):
        if isinstance(value, Model):
            self._model = value
        else:
            raise TypeError("The value is not of type Model.")

    @property
    def interaction(self):
        if not hasattr(self, "_interaction"):
            return None
        else:
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
        if not hasattr(self, "_size"):
            return None
        else:
            self._size

    @property
    def contact_forces(self):
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            point = Point(*point)
            force = force["c_np"] - force["c_nn"]
            p1 = point + w * force * 0.5
            p2 = point - w * force * 0.5
            lines.append(Line(p1, p2))
        return lines

    @property
    def compression_forces(self):
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            point = Point(*point)
            force = force["c_np"] - force["c_nn"]
            if force > 0:
                p1 = point + w * force * 0.5
                p2 = point - w * force * 0.5
                lines.append(Line(p1, p2))
        return lines

    @property
    def tension_forces(self):
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        w = frame.zaxis
        for point, force in zip(self.points, self.forces):
            point = Point(*point)
            force = force["c_np"] - force["c_nn"]
            if force < 0:
                p1 = point + w * force * 0.5
                p2 = point - w * force * 0.5
                lines.append(Line(p1, p2))
        return lines

    @property
    def friction_forces(self):
        lines = []
        if not self.forces:
            return lines
        frame = self.frame
        u, v = frame.xaxis, frame.yaxis
        for point, force in zip(self.points, self.forces):
            point = Point(*point)
            self.forces_ft_uv = (u * force["c_u"] + v * force["c_v"]) * 0.5
            p1 = point + self.forces_ft_uv
            p2 = point - self.forces_ft_uv
            lines.append(Line(p1, p2))
        return lines

    @property
    def resultant_force(self):
        if not self.forces:
            return []
        frame = self.frame
        w, u, v = frame.zaxis, frame.xaxis, frame.yaxis
        normalcomponents = [f["c_np"] - f["c_nn"] for f in self.forces]
        sum_n = sum(normalcomponents)
        sum_u = sum(f["c_u"] for f in self.forces)
        sum_v = sum(f["c_v"] for f in self.forces)
        position = Point(*centroid_points_weighted(self.points, normalcomponents))
        forcevector = (w * sum_n + u * sum_u + v * sum_v) * 0.5
        p1 = position + forcevector
        p2 = position - forcevector
        return [Line(p1, p2)]

    @property
    def display_schema(self):

        if not hasattr(self, "_display_schema"):

            face_color = (
                [0.9, 0.9, 0.9] if not self.is_support else [0.9686, 0.6157, 0.5176]
            )
            self._display_schema = OrderedDict(
                [
                    (
                        "geometry_simplified",
                        {
                            "facecolor": [0.5, 0.5, 0.5],
                            "linewidth": 1,
                            "pointsize": 20,
                            "opacity": 1.0,
                            "is_visible": True,
                            "show_faces": True,
                        },
                    ),
                    (
                        "geometry",
                        {
                            "facecolor": face_color,
                            "linecolor": [1.0, 0.0, 0.0],
                            "linewidth": 1,
                            "opacity": 0.75,
                            "is_visible": True,
                        },
                    ),
                    (
                        "frame",
                        {
                            "facecolor": [0.0, 0.0, 0.0],
                            "linecolor": [1.0, 1.0, 1.0],
                            "linewidth": 1,
                            "opacity": 1.0,
                            "is_visible": False,
                        },
                    ),
                    (
                        "aabb_mesh",
                        {
                            "facecolor": [0.0, 0.0, 0.0],
                            "linecolor": [1.0, 1.0, 1.0],
                            "linewidth": 1,
                            "opacity": 0.25,
                            "is_visible": False,
                        },
                    ),
                    (
                        "oobb_mesh",
                        {
                            "facecolor": [0.0, 0.0, 0.0],
                            "linecolor": [1.0, 1.0, 1.0],
                            "linewidth": 1,
                            "opacity": 0.25,
                            "is_visible": False,
                        },
                    ),
                ]
            )

        # --------------------------------------------------------------------------
        # create forces display schema
        # --------------------------------------------------------------------------
        if hasattr(self, "_forces"):
            for force_tuple in self._forces:
                setattr(self, force_tuple[0], force_tuple[1])

        # --------------------------------------------------------------------------
        # create fabrication display schema
        # --------------------------------------------------------------------------
        if hasattr(self, "_fabrication"):
            for fabrication_tuple in self._fabrication:
                setattr(self, fabrication_tuple[0], fabrication_tuple[1])

        return self._display_schema

    # ==========================================================================
    # Methods overriding the Element class
    # ==========================================================================

    def copy(self):
        """Makes an independent copy of all properties of this class.

        Parameters
        ----------
        all_attributes : bool, optional
            If True, all attributes are copied.
            If False, only the main properties are copied.

        Returns
        -------
        :class:`compas_model.elements.Element`
            The copied element.

        """

        new_instance = self.__class__(
            polygon=self.geometry_simplified[0],
            forces=self.forces,
            interaction=self.interaction,
            model=self.model,
            **self.attributes,
        )

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # --------------------------------------------------------------------------
        new_instance.id = list(self.id)
        new_instance.insertion = list(self.insertion)
        new_instance.frame_global = self.frame_global.copy()

        # --------------------------------------------------------------------------
        # TODO: REMOVE WHEN SCENE IS IMPLEMENTED
        # --------------------------------------------------------------------------
        new_instance._display_schema = deepcopy(self.display_schema)

        return new_instance

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
