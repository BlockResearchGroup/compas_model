from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas_model.elements.element import Element
from compas_model.elements.element_type import ElementType
from collections import OrderedDict

from compas.geometry import centroid_points
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.datastructures import Mesh
from copy import deepcopy


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
    is_support : bool
        Indicates whether the element is a support.

    """

    def __init__(self, mesh, **kwargs):

        if not isinstance(mesh, Mesh):
            raise TypeError("Mesh is not of type compas.datastructures.Mesh")

        x, y, z = centroid_points(
            [mesh.vertex_coordinates(key) for key in mesh.vertices()]
        )

        super(Block, self).__init__(
            name=ElementType.BLOCK,
            frame=Frame(Point(x, y, z), [1, 0, 0], [0, 1, 0]),
            geometry_simplified=Point(x, y, z),
            geometry=mesh,
            copy_mesh=True,
        )

        self.attributes = {}
        self.attributes.update(kwargs)

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
            "forces": self.forces,
            "fabrication": self.fabrication,
            "attributes": self.attributes,
        }

        # --------------------------------------------------------------------------
        # The attributes that are dependent on user given specifc data or geometry.
        # Because they cannot be computed from numeric inputs only, they are serialized.
        # --------------------------------------------------------------------------
        data["id"] = self.id
        data["insertion"] = self.insertion
        data["frame_global"] = self.frame_global
        data["is_support"] = self.is_support

        # The display schema can be replaced in the future by scene configuration file.
        data["display_schema"] = self.display_schema

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
        obj.forces = data["forces"]
        obj.fabrication = data["fabrication"]

        # The display schema can be replaced in the future by scene configuration file.
        obj.display_schema = OrderedDict(data["display_schema"].items())

        return obj

    # ==========================================================================
    # Attributes
    # ==========================================================================

    @property
    def face_outlines(self):

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

        face_color = (
            [0.9, 0.9, 0.9] if not self.is_support else [0.9686, 0.6157, 0.5176]
        )

        ordered_dict = OrderedDict(
            [
                (
                    "geometry_simplified",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 5,
                        "pointsize": 20,
                        "opacity": 1.0,
                        "is_visible": True,
                        "show_faces": False,
                    },
                ),
                (
                    "geometry",
                    {
                        "facecolor": face_color,
                        "linecolor": [0.0, 0.0, 0.0],
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
                (
                    "face_frames",
                    {
                        "facecolor": [0.0, 0.0, 0.0],
                        "linecolor": [1.0, 1.0, 1.0],
                        "linewidth": 1,
                        "opacity": 1.0,
                        "is_visible": False,
                    },
                ),
                (
                    "face_outlines",
                    {
                        "facecolor": [1.0, 0.0, 0.0],
                        "linecolor": [0.0, 0.0, 0.0],
                        "linewidth": 3,
                        "opacity": 1.0,
                        "is_visible": False,
                        "show_faces": False,
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

        return ordered_dict

    def copy(self):
        """Makes an independent copy of all properties of this class.

        Parameters
        ----------
        all_attributes : bool, optional
            If True, all attributes are copied, else only the main properties are copied.

        Returns
        -------
        :class:`compas_model.elements.Element`
            The copy of the element.

        """

        meshes_copy = []
        for m in self.geometry:
            meshes_copy.append(m.copy())

        new_instance = self.__class__(meshes_copy, **self.attributes)

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

    # @classmethod
    # def from_polysurface(cls, guid):
    #     """Class method for constructing a block from a Rhino poly-surface.
    #
    #     192
    #     https://github.com/compas-dev/compas/blob/c1c44cfc53d6b40badf2f7c74eae27006905ee42/src/compas_rhino/conversions/surfaces.py#L168
    #     Parameters
    #     ----------
    #     guid : str
    #         The GUID of the poly-surface.

    #     Returns
    #     -------
    #     Block
    #         The block corresponding to the poly-surface.

    #     Notes
    #     -----
    #     In Rhino, poly-surfaces are organised such that the cycle directions of
    #     the individual sub-surfaces produce normal vectors that point out of the
    #     enclosed volume. The normal vectors of the faces of the mesh, therefore
    #     also point "out" of the enclosed volume.

    #     """
    #     from compas_rhino.conversions import RhinoSurface

    #     surface = RhinoSurface.from_guid(guid)
    #     return surface.to_compas_mesh(cls)

    #

    # ==========================================================================
    # Example
    # ==========================================================================
    @classmethod
    def from_minimal_example(cls):
        """Returns a plate.

        Returns
        -------
        Block : :class:`compas_model.elements.Block`
            A mesh with a center point.

        """

        polygons = [
            Polygon(
                [
                    [2, -2, 0],
                    [2, 2, 0],
                    [2, 2, 4],
                    [2, 0, 4],
                    [2, -2, 2],
                ]
            ),
            Polygon(
                [
                    [-2, -2, 0],
                    [2, -2, 0],
                    [2, -2, 2],
                    [0, -2, 4],
                    [-2, -2, 4],
                ]
            ),
            Polygon(
                [
                    [2, -2, 2],
                    [2, 0, 4],
                    [0, -2, 4],
                ]
            ),
            Polygon(
                [
                    [-2, -2, 4],
                    [0, -2, 4],
                    [2, 0, 4],
                    [2, 2, 4],
                    [-2, 2, 4],
                ]
            ),
            Polygon(
                [
                    [2, 2, 0],
                    [-2, 2, 0],
                    [-2, 2, 4],
                    [2, 2, 4],
                ]
            ),
            Polygon(
                [
                    [-2, 2, 0],
                    [-2, -2, 0],
                    [-2, -2, 4],
                    [-2, 2, 4],
                ]
            ),
            Polygon(
                [
                    [-2, -2, 0],
                    [-2, 2, 0],
                    [2, 2, 0],
                    [2, -2, 0],
                ]
            ),
        ]

        mesh = Mesh.from_polygons(polygons)
        block = cls(mesh)
        return block
