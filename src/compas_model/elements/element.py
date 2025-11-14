from functools import reduce
from functools import wraps
from operator import mul
from typing import TYPE_CHECKING
from typing import Optional
from typing import Sequence
from typing import Type
from typing import TypeVar
from typing import Union

from compas.data import Data
from compas.datastructures import Mesh
from compas.datastructures import VolMesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Transformation
from compas_model.algorithms import brep_brep_contacts
from compas_model.algorithms import mesh_mesh_contacts
from compas_model.interactions import Contact
from compas_model.materials import Material
from compas_model.modifiers import Modifier

if TYPE_CHECKING:
    from compas_model.models import ElementNode
    from compas_model.models import Model


def reset_computed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        self: Element = args[0]
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._elementgeometry = None
        self._modelgeometry = None
        self._modeltransformation = None
        self._point = None
        self._surface_mesh = None
        self._volumetric_mesh = None
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


FeatureType = TypeVar("FeatureType", bound=Feature)


class Element(Data):
    """Base class for all elements in the model.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Brep` | :class:`compas.datastructures.Mesh`, optional
        The complete geometry of the element.
    transformation : :class:`compas.geometry.Transformation`, optional
        The transformation of the element defining its location in the model.
        This transformation is relative to the combined transformation of the ancestors of the element up to the model root.
        If no transformation is provided (default), the geometry of the element is taken as-is.
    features : list[:class:`Feature`], optional
        A list of features that define the detailed geometry of the element.
        Features are defined in the local coordinate system of the element.
    material : :class:`Material`, optional
        The material of the element.
    name : None
        The name of the element.

    Attributes
    ----------
    model : :class:`Model`
        Reference to the parent model.
    graphnode : int
        The identifier of the corresponding node in the interaction graph of the parent model.
    treenode : :class:`compas.datastructures.TreeNode`
        The node in the hierarchical element tree of the parent model.
    transformation : :class:`Transformation`
        The transformation of the element wrt its parent.
    features : list[:class:`Feature`]
        A list of features that define the detailed geometry of the element.
    modeltransformation : :class:`Transformation`, readonly
        The resolved transformation of the element wrt the model root.
    frame : :class:`compas.geometry.Frame`, readonly
        The coordinate frame corresponding to the model transformation of the element: ``Frame.from_transformation(self.modeltransformation)``
    elementgeometry : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, readonly
        The geometry of the element in element coordinates.
    modelgeometry : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`, readonly
        The geometry of the element in model coordinates: ``self.elementgeometry.transformed(self.modeltransformation)``.
    aabb : :class:`compas.geometry.Box`, readonly
        The Axis Aligned Bounding Box (AABB) of the model geometry of the element.
    obb : :class:`compas.geometry.Box`, readonly
        The Oriented Bounding Box (OBB) of the model geometry of the element.
    collision_mesh : :class:`compas.datastructures.Mesh`, readonly
        The collision mesh of the model geometry of the element.
    point : :class:`compas.geometry.Point`, readonly
        The reference location of the element.
        This is, for example, the centroid of the model geometry.
    surface_mesh : :class:`Mesh`, readonly
        A triangle mesh representing the surface boundary of the model geometry of the element, for example for FEA.
    volumetric_mesh : :class:`VolMesh`, readonly
        A tetrahedral mesh representing the internal volume of the model geometry of the element, for example for FEA.

    Notes
    -----


    """

    model: "Model"
    treenode: "ElementNode"
    graphnode: int

    @property
    def __data__(self) -> dict:
        return {
            "transformation": self.transformation,
            "features": self.features,
            "name": self.name,
            "material": self._material,
        }

    def __init__(
        self,
        geometry: Optional[Union[Brep, Mesh]] = None,
        transformation: Optional[Transformation] = None,
        features: Optional[Sequence[Union[Feature, FeatureType]]] = None,
        material: Optional[Material] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(name=name)

        self.model = None  # type: ignore
        self.treenode = None  # type: ignore
        self.graphnode = None  # type: ignore

        self._transformation = transformation
        self._geometry = geometry
        self._features = list(features or [])
        self._material = None
        if material:
            self.material = material

        self._elementgeometry = None
        self._modelgeometry = None
        self._modeltransformation = None

        self._point = None
        self._aabb = None
        self._obb = None
        self._collision_mesh = None
        self._surface_mesh = None
        self._volumetric_mesh = None

        self._is_dirty = True

    # this is not entirely correct
    def __repr__(self) -> str:
        return f"Element(frame={self.frame!r}, name={self.name})"

    def __str__(self) -> str:
        return f"<Element {self.name}>"

    @property
    def geometry(self) -> Optional[Union[Mesh, Brep]]:
        return self._geometry

    @geometry.setter
    @reset_computed
    def geometry(self, geometry: Union[Mesh, Brep]) -> None:
        self._geometry = geometry

    @property
    def transformation(self) -> Union[Transformation, None]:
        return self._transformation

    @transformation.setter
    @reset_computed
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    @property
    def frame(self) -> Frame:
        return Frame.from_transformation(self.modeltransformation)

    @property
    def material(self) -> Union[Material, None]:
        if self._material:
            return self.model._materials[self._material]

    @material.setter
    def material(self, material: Union[Material, str]) -> None:
        if isinstance(material, Material):
            self._material = str(material.guid)
        elif isinstance(material, str):
            self._material = material
        else:
            raise TypeError("material must be a Material or a str")

    @property
    def parentnode(self) -> "ElementNode":
        return self.treenode.parent  # type: ignore

    @property
    def parent(self) -> Union["Element", None]:
        if not self.parentnode.is_root:
            return self.parentnode.element  # type: ignore

    @property
    def childnodes(self) -> list["ElementNode"]:
        return self.treenode.children

    @property
    def children(self) -> list["Element"]:
        return [child.element for child in self.childnodes]  # type: ignore

    @property
    def features(self) -> list[Feature]:
        return self._features

    # ==========================================================================
    # Computed attributes
    # ==========================================================================

    @property
    def elementgeometry(self) -> Union[Brep, Mesh]:
        if self._elementgeometry is None:
            self._elementgeometry = self.compute_elementgeometry()
        return self._elementgeometry

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

    @property
    def surface_mesh(self) -> Mesh:
        if not self._surface_mesh:
            self._surface_mesh = self.compute_surface_mesh()
        return self._surface_mesh

    @property
    def volumetric_mesh(self) -> VolMesh:
        if not self._volumetric_mesh:
            self._volumetric_mesh = self.compute_volumetric_mesh()
        return self._volumetric_mesh

    # ==========================================================================
    # Abstract methods
    # ==========================================================================

    def compute_elementgeometry(self, include_features: bool = False) -> Union[Brep, Mesh]:
        """Compute the geometry of the element in local coordinates.

        This is the parametric representation of the element,
        without considering its location in the model or its interaction(s) with connected elements.

        Parameters
        ----------
        include_features : bool, optional
            If True, the features should be included in the element geometry.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        raise NotImplementedError

    def compute_modeltransformation(self) -> Transformation:
        """Compute the transformation to model coordinates of this element
        based on its position in the spatial hierarchy of the model.

        Returns
        -------
        :class:`compas.geometry.Transformation`

        """
        stack = []

        if self.transformation:
            stack.append(self.transformation)

        parent = self.parent

        while parent:
            if parent.transformation:
                stack.append(parent.transformation)
            parent = parent.parent

        if self.model.transformation:
            stack.append(self.model.transformation)

        if stack:
            return reduce(mul, stack[::-1])
        return Transformation()

    def compute_modelgeometry(self) -> Union[Brep, Mesh]:
        """Compute the geometry of the element in model coordinates and taking into account the effect of interactions with connected elements.

        Returns
        -------
        :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Brep`

        """
        xform = self.modeltransformation
        modelgeometry = self.elementgeometry.transformed(xform)

        for nbr in self.model.graph.neighbors_in(self.graphnode):
            modifiers: list[Modifier] = self.model.graph.edge_attribute((nbr, self.graphnode), name="modifiers")  # type: ignore
            if modifiers:
                source = self.model.graph.node_element(nbr)
                for modifier in modifiers:
                    modelgeometry = modifier.apply(source, modelgeometry)

        # self.is_dirty = False

        return modelgeometry

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        """Computes the Axis Aligned Bounding Box (AABB) of the geometry of the element.

        Parameters
        ----------
        inflate : float, optional
            Inflate the bounding box by this scaling factor.

        Returns
        -------
        :class:`compas.geometry.Box`
            The AABB of the element.

        """
        raise NotImplementedError

    def compute_obb(self, inflate: float = 1.0) -> Box:
        """Computes the Oriented Bounding Box (OBB) of the geometry of the element.

        Parameters
        ----------
        inflate : float, optional
            Inflate the bounding box by this scaling factor.

        Returns
        -------
        :class:`compas.geometry.Box`
            The OBB of the element.

        """
        raise NotImplementedError

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        """Computes the collision geometry of the geometry of the element.

        Parameters
        ----------
        inflate : float, optional
            Inflate the bounding box by this scaling factor.

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

    def compute_surface_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> Mesh:
        """Computes the triangulated surface mesh of the element's model geometry.

        Parameters
        ----------
        meshsize_min : float, optional
            Minimum size of the mesh elements.
        meshsize_max : float, optional
            Maximum size of the mesh elements.

        Returns
        -------
        :class:`compas.datastructures.Mesh`
            The triangular mesh.

        """
        raise NotImplementedError

    def compute_volumetric_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> VolMesh:
        """Computes the tetrahedral volumetric mesh of the element's model geometry.

        Parameters
        ----------
        meshsize_min : float, optional
            Minimum size of the mesh elements.
        meshsize_max : float, optional
            Maximum size of the mesh elements.

        Returns
        -------
        :class:`compas.geometry.VolMesh`
            The polyhedral mesh.

        """
        raise NotImplementedError

    def compute_contacts(
        self,
        other: "Element",
        tolerance: float = 1e-6,
        minimum_area: float = 1e-2,
        contacttype: Type[Contact] = Contact,
    ) -> list[Contact]:
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
        if isinstance(self.modelgeometry, Mesh) and isinstance(other.modelgeometry, Mesh):
            return mesh_mesh_contacts(
                self.modelgeometry,
                other.modelgeometry,
                tolerance=tolerance,
                minimum_area=minimum_area,
                contacttype=contacttype,
            )
        elif isinstance(self.modelgeometry, Brep) and isinstance(other.modelgeometry, Brep):
            return brep_brep_contacts(
                self.modelgeometry,
                other.modelgeometry,
                tolerance=tolerance,
                minimum_area=minimum_area,
                contacttype=contacttype,
            )
        raise NotImplementedError

    def apply_features(self) -> Union[Mesh, Brep]:
        """Apply the features to the (base) geometry.

        Returns
        -------
        Mesh | Brep

        """
        raise NotImplementedError

    # ==========================================================================
    # Transformations
    # ==========================================================================

    @reset_computed
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
        if self.transformation:
            self.transformation = transformation * self.transformation
        else:
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
        """Add a feature to the list of features of the element.

        Parameters
        ----------
        feature : :class:`Feature`
            A feature

        Returns
        -------
        None

        """
        self.features.append(feature)
