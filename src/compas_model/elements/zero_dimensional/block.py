from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_model.elements.element import Element
from collections import OrderedDict

from compas.geometry import centroid_points
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.datastructures import Mesh


class Block(Element):
    """A data structure for the individual blocks of a discrete element assembly.

    The implementation is inspired by the compas_assembly block class:
    https://github.com/BlockResearchGroup/compas_assembly/blob/main/src/compas_assembly/datastructures/block.py

    Parameters
    ----------
    mesh : :class:`compas.datastructures.Mesh`
        The mesh representing the block.

    Attributes
    ----------
    face_frames : list[:class:`compas.geometry.Frame`] or None
        A list of frames representing the faces of the geometry.
    face_polygons : list[:class:`compas.geometry.Polygon`] or None
        A list of polygons representing the faces of the geometry.
    top : int
        The identifier of the top face of the block.
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

    def __init__(self, mesh, **kwargs):
        if not isinstance(mesh, Mesh):
            raise TypeError("Mesh is not of type compas.datastructures.Mesh")

        x, y, z = centroid_points(
            [mesh.vertex_coordinates(key) for key in mesh.vertices()]
        )

        super(Block, self).__init__(
            name="block",
            frame=Frame(Point(x, y, z), [1, 0, 0], [0, 1, 0]),
            geometry_simplified=Point(x, y, z),
            geometry=mesh,
            copy_geometry=True,
            **kwargs,
        )

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
            # "attributes": self.attributes,
        }

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        data["id"] = self.id
        data["insertion"] = self.insertion
        data["is_support"] = self.is_support

        # The display schema can be replaced in the future by scene configuration file.
        data["display_schema"] = self.display_schema

        return data

    @classmethod
    def from_data(cls, data):
        obj = cls(
            mesh=data["geometry"][0],
            # **data["attributes"],
        )

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        obj.frame = data["frame"]
        obj.id = data["id"]
        obj.insertion = data["insertion"]
        obj.is_support = data["is_support"]

        # The display schema can be replaced in the future by scene configuration file.
        obj._display_schema = OrderedDict(data["display_schema"].items())

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def face_polygons(self):
        if hasattr(self, "_face_polygons"):
            return self._face_polygons

        # --------------------------------------------------------------------------
        # get polylines from the mesh faces
        # --------------------------------------------------------------------------
        self._face_polygons = []
        for g in self.geometry:
            if isinstance(g, Mesh):
                temp = self.geometry[0].to_polygons()
                self._face_polygons = []
                for point_list in temp:
                    self._face_polygons.append(Polygon(point_list))

        return self._face_polygons

    @property
    def face_frames(self):
        if hasattr(self, "_face_frames"):
            return self._face_frames

        self._face_frames = []

        for g in self.geometry:
            if isinstance(g, Mesh):
                mesh = g

            for fkey in mesh.faces():
                xyz = mesh.face_coordinates(fkey)
                o = mesh.face_center(fkey)
                w = mesh.face_normal(fkey)
                u = [
                    xyz[1][i] - xyz[0][i] for i in range(3)
                ]  # align with longest edge instead?
                v = cross_vectors(w, u)
                frame = Frame(o, u, v)
                self._face_frames.append(frame)

        return self._face_frames

    @property
    def top(self):
        if hasattr(self, "_top"):
            return self._top
        z = [0, 0, 1]
        faces = list(self.geometry[0].faces())
        normals = [self.geometry[0].face_normal(face) for face in faces]
        _top = sorted(zip(faces, normals), key=lambda x: dot_vectors(x[1], z))[-1][0]
        return _top

    @property
    def display_schema(self):
        face_color = [0.9, 0.9, 0.9] if not self.is_support else [0.968, 0.615, 0.517]
        lines_weight = 5

        return OrderedDict(
            [
                ("geometry_simplified", {"is_visible": True}),
                (
                    "geometry",
                    {"facecolor": face_color, "opacity": 0.75, "is_visible": True},
                ),
                ("frame", {}),
                ("aabb", {"opacity": 0.25}),
                ("oobb", {"opacity": 0.25}),
                ("face_polygons", {"linewidth": lines_weight, "show_faces": False}),
                ("face_frames", {"linewidth": lines_weight}),
            ]
        )

    # ==========================================================================
    # Conversions
    # ==========================================================================

    @classmethod
    def from_rhino_guid(cls, guid):
        """Class method for constructing a block from a Rhino guid.

        Parameters
        ----------
        guid : str
            The GUID of the mesh.

        Returns
        -------
        Block
            The block corresponding to the Rhino mesh.

        """
        from Rhino import RhinoDoc  # noqa
        from compas_rhino.conversions import mesh_to_compas

        rhino_mesh = RhinoDoc.ActiveDoc.Objects.Find(guid)
        compas_mesh = mesh_to_compas(rhino_mesh.Geometry)
        return cls(compas_mesh)

    @classmethod
    def from_rhino(cls):
        """Class method for constructing a block from a Rhino mesh.
        You need to run thino method in Rhino Python Editor."""
        from Rhino.Input.Custom import GetObject  # noqa
        from Rhino.DocObjects import ObjectType  # noqa

        # Prompt the user to select meshes
        go = GetObject()
        go.SetCommandPrompt("Select meshes.")
        go.GeometryFilter = ObjectType.Mesh
        go.GetMultiple(1, 0)

        block_elements = []
        for i in range(go.ObjectCount):
            block_elements.append(Block.from_rhino_guid(go.Object(i).ObjectId))

        return block_elements

    @classmethod
    def from_shape(cls, shape, **kwargs):
        """Class method for constructing a block from a Rhino box."""
        return cls(Mesh.from_shape(shape))
