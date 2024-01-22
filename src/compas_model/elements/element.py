from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.data import Data
from compas.geometry import Frame
from compas.geometry import Vector
from compas.geometry import Box
from abc import abstractmethod


class Element(Data):
    """Base class for model elements.

    WARNING: Do not use this class directly; instead, use a subclass such as Beam, Block, Plate, Interface, etc.

    Parameters
    ----------
    name : str, optional
        Name of the element
    frame : :class:`compas.geometry.Frame`, optional
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry_simplified : list[Any] or Any
        A simplified geometrical shape, e.g. a central Line for a beam, a polygon for a plate.
    geometry : list[Any] or Any
        Closed shape(s) representing the actual geometry of the element, e.g. a mesh for a block, a box for a beam.
    kwargs (dict, optional):
        Additional keyword arguments.

    Attributes
    ----------
    guid : str, read-only
        The globally unique identifier of the object.
        The guid is generated with ``uuid.uuid4()``.
    name : str
        The name of the object.
        This name is not necessarily unique and can be set by the user.
        The default value is the object's class name: ``self.__class__.__name__``.
    frame : :class:`compas.geometry.Frame`, read-only
        Local coordinate of the object, default is :class:`compas.geometry.Frame.WorldXY()`.
    geometry : list[Any] or Any, read-only
        Closed shape(s) representing the actual geometry of the element, e.g. a mesh for a block, a box for a beam.
    geometry_simplified : list[Any] or Any, read-only
        A simplified geometrical shape, e.g. a central Line for a beam, a polygon(s) for a plate.
    aabb : :class:`compas.geometry.Box`, read-only
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`, read-only
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, read-only
        The collision geometry of the element.
    dimensions : list, read-only
        The dimensions of the element.
    features : dict
        These are custom geometrical objects added to the elements through operations made by the user.
        For example, a cutting shape for boolean difference operations, text identifiers.
    insertion : :class:`compas.geometry.Vector`
        The insertion vector of the element. Default is (0, 0, -1), representing a downwards insertion.
        This attribute is often used for simulating an assembly sequence.
    node : :class:`compas_model.model.ElementNode`
        The node in the model tree containing the element.

    """

    def __init__(
        self,
        name=None,
        frame=None,
        geometry=None,
        geometry_simplified=None,
    ):

        name = name.lower() if name else str.lower(self.__class__.__name__)
        super(Element, self).__init__(name=name)

        self._frame = frame if frame.copy() else Frame.worldXY()
        self._geometry = self._copy_geometries(geometry) if geometry else []
        self._geometry_simplified = (
            self._copy_geometries(geometry_simplified) if geometry_simplified else []
        )
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._dimensions = []
        self._features = {}
        self._insertion = Vector(0, 0, -1)
        self._node = None

    def __repr__(self):
        return """{0} {1}""".format(self.name, self.guid)

    def __str__(self):
        return self.__repr__()

    def _copy_geometries(self, geometries):
        """
        Helper function to copy geometries.

        Returns
        -------
        list

        """
        if isinstance(geometries, list):
            copied_geometries = []
            for g in geometries:
                copied_geometries.append(g)
            return copied_geometries
        else:
            return geometries.copy()

    # ==========================================================================
    # Attributes.
    # ==========================================================================

    @property
    def frame(self):
        return self._frame

    @property
    def geometry_simplified(self):
        return self._geometry_simplified

    @property
    def geometry(self):
        return self._geometry

    @property
    def aabb(self):
        if not self._aabb:
            self.compute_aabb()
        return self._aabb

    @property
    def obb(self):
        if not self._obb:
            self.compute_obb()
        return self._obb

    @property
    def collision_mesh(self):
        if not self._collision_mesh:
            self.compute_collision_mesh()
        return self._collision_mesh

    @property
    def dimensions(self):
        if not type(self.obb) is Box:
            raise TypeError("OBB is not set as a Box.")
        return [self.obb.width, self.obb.height, self.obb.depth]

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, value):
        if not type(value) is dict:
            raise TypeError("Features must be a dictionary.")
        self.features = value

    @property
    def insertion(self):
        return self._insertion

    @insertion.setter
    def insertion(self, value):
        if not type(value) is Vector:
            raise TypeError("Insertion must be a Vector.")
        self._insertion = value

    @property
    def node(self):
        if self._node is None:
            raise ValueError("Node is not set.")
        return self._node

    @node.setter
    def node(self, value):
        self._node = value

    # ==========================================================================
    # Templated methods to provide minimal information for:
    # aabb
    # obb
    # geometry_collision
    # transform
    # ==========================================================================

    @abstractmethod
    def compute_aabb(self, inflate=0.0):
        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    @abstractmethod
    def compute_obb(self, inflate=0.0):
        """Computes the Oriented Bounding Box (OBB) of the element.

        Attributes
        ----------
        inflate : float
            Offset of box to avoid floating point errors.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    @abstractmethod
    def compute_collision_mesh(self):
        """Computes the collision geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """

        raise NotImplementedError

    @abstractmethod
    def transform(self, transformation):
        """Transforms all the attrbutes of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied to the Element's geometry and frames.

        Returns
        -------
        None

        """

        self.frame.transform(transformation)
        [g.transform(transformation) for g in self.geometry_simplified]
        [g.transform(transformation) for g in self.geometry]
        self.aabb.transform(transformation)
        self.obb.transform(transformation)
        self.collision_mesh.transform(transformation)

        # Expand this list of transformations according to the attributes of the class.
        raise NotImplementedError

    # ==========================================================================
    # Public methods.
    # ==========================================================================

    def transformed(self, transformation):
        """Creates a transformed copy of the class.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of an element.

        Returns
        -------
        :class:`compas_model.elements.Element`
            A new instance of the Element with the specified transformation applied.

        """
        new_instance = self.copy()
        new_instance.transform(transformation)
        return new_instance
