from functools import reduce
from functools import wraps
from operator import mul
from typing import TYPE_CHECKING
from typing import Optional
from typing import Union

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Shape
from compas.geometry import Transformation
from compas_model.algorithms import mesh_mesh_collision
from compas_model.algorithms import mesh_mesh_contacts
from compas_model.interactions import Contact
from compas_model.interactions import Modifier
from compas_model.materials import Material

if TYPE_CHECKING:
    from compas_model.elements import Element
    from compas_model.models import ElementNode
    from compas_model.models import Model


def reset_computed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self: Element = args[0]
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._geometry = None
        self._modelgeometry = None
        self._modeltransformation = None
        self._point = None
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
    def __data__(self) -> dict:
        return {}

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)

    def apply(self, shape: Union[Mesh, Brep]) -> Union[Mesh, Brep]:
        """Apply the feature to the given shape, which represents the base geometry of the host element of the feature."""
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
    graphnode : int
        The identifier of the corresponding node in the interaction graph of the parent model.
    treenode : :class:`compas.datastructures.TreeNode`
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
    is_dirty : bool
        Flag to indicate that modelgeometry has to be recomputed.

    """

    model: "Model"
    treenode: "ElementNode"
    graphnode: int

    @property
    def __data__(self) -> dict:
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
        geometry: Optional[Union[Shape, Brep, Mesh]] = None,
        frame: Optional[Frame] = None,
        transformation: Optional[Transformation] = None,
        features: Optional[list[Feature]] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name)

        self.model = None
        self.treenode = None
        self.graphnode = None

        self._frame = frame
        self._transformation = transformation
        self._geometry = geometry  # this is same as elementgeometry
        self._features = features or []
        self._material = None

        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._modelgeometry = None
        self._modeltransformation = None
        self._point = None

        self.include_features = False
        self.inflate_aabb = 0.0
        self.inflate_obb = 0.0

        self._is_dirty = True

    # this is not entirely correct
    def __repr__(self) -> str:
        return f"Element(frame={self.frame!r}, name={self.name})"

    def __str__(self) -> str:
        return f"<Element {self.name}>"

    @property
    def frame(self) -> Union[Frame, None]:
        return self._frame

    @frame.setter
    @reset_computed
    def frame(self, frame: Frame) -> None:
        self._frame = frame

    @property
    def transformation(self) -> Union[Transformation, None]:
        return self._transformation

    @transformation.setter
    @reset_computed
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    @property
    def material(self) -> Union[Material, None]:
        return self._material

    @property
    def parent(self) -> "ElementNode":
        return self.treenode.parent

    @property
    def features(self) -> list[Feature]:
        return self._features

    @property
    def is_dirty(self) -> bool:
        return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool):
        self._is_dirty = value

        if value:
            elements: list[Element] = list(self.model.elements())
            for neighbor in self.model.graph.neighbors_out(self.graphnode):
                elements[neighbor].is_dirty = value

    # ==========================================================================
    # Computed attributes
    # ==========================================================================

    @property
    def elementgeometry(self) -> Union[Brep, Mesh]:
        if self._geometry is None:
            self._geometry = self.compute_elementgeometry()
        return self._geometry

    @property
    def modeltransformation(self) -> Transformation:
        if self._modeltransformation is None:
            self._modeltransformation = self.compute_modeltransformation()
        return self._modeltransformation

    @property
    def modelgeometry(self) -> Union[Brep, Mesh]:
        if self._modelgeometry is None:
            self._modelgeometry = self.compute_modelgeometry()
        return self._modelgeometry

    @property
    def aabb(self) -> Box:
        if not self._aabb:
            self._aabb = self.compute_aabb()
        return self._aabb

    @property
    def obb(self) -> Box:
        if not self._obb:
            self._obb = self.compute_obb()
        return self._obb

    @property
    def dimensions(self) -> tuple[float, float, float]:
        return self.obb.width, self.obb.height, self.obb.depth

    @property
    def collision_mesh(self) -> Mesh:
        if not self._collision_mesh:
            self._collision_mesh = self.compute_collision_mesh()
        return self._collision_mesh

    @property
    def point(self) -> Point:
        if not self._point:
            self._point = self.compute_point()
        return self._point

    # ==========================================================================
    # Abstract methods
    # ==========================================================================

    def compute_elementgeometry(self) -> Union[Brep, Mesh]:
        """Compute the geometry of the element in local coordinates.

        This is the parametric representation of the element,
        without considering its location in the model or its interaction(s) with connected elements.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        raise NotImplementedError

    def apply_features(self) -> None:
        """Apply the features to the (base) geometry.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def compute_modeltransformation(self) -> Transformation:
        """Compute the transformation to model coordinates of this element
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

        matrices = [Transformation.from_frame(f) for f in frame_stack]

        if matrices:
            modeltransformation = reduce(mul, matrices[::-1])
        else:
            modeltransformation = Transformation()

        if self.transformation:
            modeltransformation = modeltransformation * self.transformation

        return modeltransformation

    def compute_modelgeometry(self) -> Union[Brep, Mesh]:
        """Compute the geometry of the element in model coordinates and taking into account the effect of interactions with connected elements.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        xform = self.modeltransformation
        modelgeometry = self.elementgeometry.transformed(xform)

        # Modifiers updated
        # TODO: contacts this needs to be updated

        graph = self.model.graph
        for neighbor in graph.neighbors_in(self.graphnode):
            modifiers: Union[list[Modifier], None] = graph.edge_attribute((neighbor, self.graphnode), "modifiers")

            if modifiers:
                for modifer in modifiers:
                    modelgeometry = modifer.apply(modelgeometry)

        self.is_dirty = False

        return modelgeometry

    def compute_aabb(self) -> Box:
        """Computes the Axis Aligned Bounding Box (AABB) of the geometry of the element.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    def compute_obb(self) -> Box:
        """Computes the Oriented Bounding Box (OBB) of the geometry of the element.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    def compute_collision_mesh(self) -> Mesh:
        """Computes the collision geometry of the geometry of the element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The collision geometry of the element.

        """
        raise NotImplementedError

    def compute_point(self) -> Point:
        """Computes a reference point for the element geometry (e.g. the centroid).

        Returns
        -------
        :class:`compas.geometry.Point`
            The reference point.

        """
        raise NotImplementedError

    # ==========================================================================
    # Transformations
    # ==========================================================================

    def transform(self, transformation: Transformation) -> None:
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

    def transformed(self, transformation: Transformation) -> "Element":
        """Creates a transformed copy of the element.

        Parameters
        ----------
        transformation : :class:`compas.geometry.Transformation`:
            The transformation to be applied to the copy of the element.

        Returns
        -------
        :class:`compas_model.elements.Element`

        """
        element: Element = self.copy()
        element.transform(transformation)
        return element

    # ==========================================================================
    # Methods
    # ==========================================================================

    def add_feature(self, feature: Feature) -> None:
        """Add a feature to the list of features of the lement.

        Parameters
        ----------
        feature : :class:`Feature`
            A feature

        Returns
        -------
        None

        """
        self._features.append(feature)

    def collision(self, other: "Element") -> Mesh:
        """Compute the collision between this element and another element.

        Parameters
        ----------
        other : :class:`Element`
            The other element.

        Returns
        -------
        :class:`compas.datastructures.Mesh`

        """
        # perhaps we should check the type of self.modelgeometry to decide which collision algorithm to use
        mesh_mesh_collision()

    def contacts(self, other: "Element", tolerance: float = 1e-6, minimum_area: float = 1e-2) -> list[Contact]:
        """Compute the contacts between this element and another element.

        Parameters
        ----------
        other : :class:`Element`
            The other element.
        tolerance : float, optional
            A distance tolerance.
        minimum_area : float, optional
            The minimum area of the contact polygon.

        Returns
        -------
        list[:class:`Contact`]

        """
        # perhaps we should check the type of self.modelgeometry to decide which contact algorithm to use
        return mesh_mesh_contacts(
            self.modelgeometry,
            other.modelgeometry,
            tolerance=tolerance,
            minimum_area=minimum_area,
        )

    def add_modifier(self, target_element: "Element", modifier_type: type[Modifier] = None, **kwargs) -> Modifier:
        """Computes the modifier to be applied to the target element.

        Parameters
        ----------
        target_element : Element
            The target element creates a modifier from a method with a neighbor Element name. For example _add_modifier_with_beam, _add_modifier_with_plate, etc.
        modifier_type : type[Modifier] | None
            The type of Modifier to be used. If not provided, the default modifier will be used.
        kwargs : dict
            The keyword arguments to be passed to the contact interaction.

        Returns
        -------
        Modifier
            The ContactInteraction that is applied to the neighboring element. One pair can have one or multiple variants.

        Raises
        ------
        ValueError
            If the target element type is not supported.
        """
        # Traverse up to the class one before the Element class
        parent_class = target_element.__class__
        while parent_class.__bases__[0].__name__ != "Element":
            parent_class = parent_class.__bases__[0]

        parent_class_name = parent_class.__name__.lower().replace("element", "")
        method_name = f"_add_modifier_with_{parent_class_name}"
        method = getattr(self, method_name, None)

        if method is None:
            raise ValueError(f"Unsupported target element type: {type(target_element)}")
        return method(target_element, modifier_type, **kwargs)
