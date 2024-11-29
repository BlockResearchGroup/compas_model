import compas

if not compas.IPY:
    from typing import TYPE_CHECKING
    from typing import Union  # noqa: F401

    if TYPE_CHECKING:
        from compas_model.models import ElementNode  # noqa: F401

from functools import reduce
from functools import wraps
from operator import mul

import compas.datastructures  # noqa: F401
import compas.geometry
from compas.data import Data
from compas.geometry import Transformation


def reset_computed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = None
        return f(*args, **kwargs)

    return wrapper


class Feature(Data):
    """Base class for all element features.

    Parameters
    ----------
    name : str, optional
        The name of the feature.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(Feature, self).__init__(name=name)

    def apply(self, shape):
        # type: (compas.datastructures.Mesh | compas.geometry.Brep) -> compas.datastructures.Mesh | compas.geometry.Brep
        raise NotImplementedError


class Element(Data):
    """Base class for all elements in the model.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Shape` | :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`, optional
        The complete geometry of the element.
    frame : None, default WorldXY
        The frame of the element.
    name : None
        The name of the element.

    Attributes
    ----------
    graph_node : int
        The identifier of the corresponding node in the interaction graph of the parent model.
    tree_node : :class:`compas.datastructures.TreeNode`
        The node in the hierarchical element tree of the parent model.
    frame : :class:`compas.geometry.Frame`
        The local coordinate frame of the element.
    geometry : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, readonly
        The geometry of the element, computed from the base shape and its features.
    aabb : :class:`compas.geometry.Box`, readonly
        The Axis Aligned Bounding Box (AABB) of the element.
    obb : :class:`compas.geometry.Box`, readonly
        The Oriented Bounding Box (OBB) of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, readonly
        The collision geometry of the element.
    features : list[:class:`Feature`]
        A list of features that define the detailed geometry of the element.
    include_features : bool
        Include the features in the element geometry.
    inflate_aabb : float
        Scaling factor to inflate the AABB with.
    inflate_obb : float
        Scaling factor to inflate the OBB with.

    """

    @property
    def __data__(self):
        # type: () -> dict
        # note that the material can/should not be added here,
        # because materials should be added by/in the context of a model
        # and becaue this would also require a custom "from_data" classmethod.
        return {
            "frame": self.frame,
            "transformation": self.transformation,
            "name": self.name,
        }

    def __init__(
        self,
        geometry=None,  # type: compas.geometry.Shape | compas.geometry.Brep | compas.datastructures.Mesh | None
        frame=None,  # type: compas.geometry.Frame | None
        transformation=None,  # type: compas.geometry.Transformation | None
        name=None,  # type: str | None
    ):  # type: (...) -> None
        super(Element, self).__init__(name=name)
        self.graph_node = None  # type: int | None
        self.tree_node = None  # type: ElementNode | None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = geometry
        self._frame = frame
        self._transformation = transformation
        self._worldtransformation = None
        self._material = None
        self.features = []  # type: list[Feature]
        self.include_features = False
        self.inflate_aabb = 0.0
        self.inflate_obb = 0.0

    # this is not entirely correct
    def __repr__(self):
        # type: () -> str
        return "Element(frame={!r}, name={})".format(self.frame, self.name)

    def __str__(self):
        # type: () -> str
        return "<Element {}>".format(self.name)

    @property
    def frame(self):
        # type: () -> compas.geometry.Frame | None
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._worldtransformation = None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = None
        self._frame = frame

    @property
    def transformation(self):
        # type: () -> compas.geometry.Transformation | None
        """
        Transformation of the element wrt its own frame.
        When this property is changed, all computed properties have to be recomputed.
        """
        return self._transformation

    @transformation.setter
    def transformation(self, transformation):
        self._worldtransformation = None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = None
        self._transformation = transformation

    @property
    def material(self):
        return self._material

    @property
    def parent(self):
        return self.tree_node.parent

    # ==========================================================================
    # Computed attributes
    # ==========================================================================

    # it might be easier to just always compute these

    @property
    def worldtransformation(self):
        # type: () -> compas.geometry.Transformation
        if self._worldtransformation is None:
            self._worldtransformation = self.compute_worldtransformation()
        return self._worldtransformation

    @property
    def geometry(self):
        # type: () -> ...
        if self._geometry is None:
            self._geometry = self.compute_geometry()
        return self._geometry

    @property
    def aabb(self):
        # type: () -> compas.geometry.Box
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return self._aabb

    @property
    def obb(self):
        # type: () -> compas.geometry.Box
        if not self._obb:
            self._obb = self.compute_obb()
        return self._obb

    @property
    def dimensions(self):
        # type: () -> tuple[float, float, float]
        return self.obb.width, self.obb.height, self.obb.depth

    @property
    def collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        if not self._collision_mesh:
            self._collision_mesh = self.compute_collision_mesh()
        return self._collision_mesh

    # ==========================================================================
    # Abstract methods
    # ==========================================================================

    def compute_worldtransformation(self):
        # type: () -> compas.geometry.Transformation
        """Compute the transformation to world coordinates of this element
        based on its position in the spatial hierarchy of the model.

        Returns
        -------
        :class:`compas.geometry.Transformation`

        """
        frame_stack = []

        if self.frame:
            frame_stack.append(self.frame)

        parent = self.parent

        while parent:
            if parent.element:
                if parent.element.frame:
                    frame_stack.append(parent.element.frame)
            parent = parent.parent

        frame = self.tree_node.tree.model.frame
        if frame:
            frame_stack.append(frame)

        matrices = [Transformation.from_frame(f) for f in frame_stack]

        if matrices:
            worldtransformation = reduce(mul, matrices[::-1])
        else:
            worldtransformation = Transformation()

        if self.transformation:
            worldtransformation = worldtransformation * self.transformation

        return worldtransformation

    def compute_geometry(self):
        # type: () -> compas.datastructures.Mesh | compas.geometry.Brep
        """Compute the geometry of the element.

        Implementations of this method should transform the geometry to world coordinates,
        using `self.worldtransformation`.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        raise NotImplementedError

    def compute_aabb(self):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Axis Aligned Bounding Box (AABB) of the element.

        Implementations of this method should base the computation on the geometry in world coordinates.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    def compute_obb(self):
        # type: (float | None) -> compas.geometry.Box
        """Computes the Oriented Bounding Box (OBB) of the element.

        Implementations of this method should base the computation on the geometry in world coordinates.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    def compute_collision_mesh(self):
        # type: () -> compas.datastructures.Mesh
        """Computes the collision geometry of the element.

        Implementations of this method should base the computation on the geometry in world coordinates.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        raise NotImplementedError

    # ==========================================================================
    # Transformations
    # ==========================================================================

    def transform(self, transformation):
        # type: (compas.geometry.Transformation) -> None
        """Transforms the element.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`
            The transformation to be applied.

        Returns
        -------
        None

        """
        self.transformation = transformation

    def transformed(self, transformation):
        # type: (compas.geometry.Transformation) -> Element
        """Creates a transformed copy of the element.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of the element.

        Returns
        -------
        :class:`compas_model.elements.Element`

        """
        element = self.copy()  # type: Element
        element.transform(transformation)
        return element

    # ==========================================================================
    # Methods
    # ==========================================================================

    def add_feature(self, feature):
        # type: (Feature) -> None
        """Add a feature to the list of features of the lement.

        Parameters
        ----------
        feature : :class:`Feature`
            A feature

        Returns
        -------
        None

        """
        self.features.append(feature)
