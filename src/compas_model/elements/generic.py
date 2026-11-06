from math import degrees
from typing import Optional
from typing import cast

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Point
from compas.geometry import Shape
from compas.geometry import Transformation
from compas.tolerance import TOL
from compas_model.geometry import is_geometry_empty
from compas_model.materials import Material

from .element import Element
from .element import Feature


def _inflated(box: Box, factor: float) -> Box:
    if factor <= 0:
        raise ValueError("The inflation factor should be greater than zero.")
    if factor != 1.0:
        box.xsize *= factor
        box.ysize *= factor
        box.zsize *= factor
    return box


class MeshElement(Element):
    """A context-free element represented by a COMPAS mesh.

    Parameters
    ----------
    geometry
        The mesh in element-local coordinates.
    transformation
        The transformation from element-local to parent coordinates.
    features
        Features applied in order before model transformations and modifiers.
    material
        The element material.
    name
        The element name.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["geometry"] = self.geometry
        return data

    def __init__(
        self,
        geometry: Mesh,
        transformation: Optional[Transformation] = None,
        features: Optional[list[Feature]] = None,
        material: Optional[Material] = None,
        name: Optional[str] = None,
    ) -> None:
        if not isinstance(geometry, Mesh):
            raise TypeError("MeshElement geometry should be a Mesh.")
        super().__init__(geometry=geometry, transformation=transformation, features=features, material=material, name=name)

    @property
    def is_empty(self) -> bool:
        """bool: Whether the evaluated mesh has no vertices."""
        return is_geometry_empty(self.final_geometry)

    def compute_base_geometry(self) -> Mesh:
        geometry = self.geometry
        if not isinstance(geometry, Mesh):
            raise TypeError("MeshElement geometry should be a Mesh.")
        return geometry.copy()

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        if self.is_empty:
            raise ValueError("An empty element has no axis-aligned bounding box.")
        return _inflated(self.final_geometry.aabb, inflate)

    def compute_obb(self, inflate: float = 1.0) -> Box:
        if self.is_empty:
            raise ValueError("An empty element has no oriented bounding box.")
        return _inflated(self.final_geometry.obb, inflate)

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        if inflate != 1.0:
            raise NotImplementedError("Inflated collision meshes are not supported; inflate the broad-phase bounds instead.")
        return cast(Mesh, self.final_geometry).copy()

    def compute_point(self) -> Point:
        x, y, z = cast(Mesh, self.final_geometry).centroid()
        return Point(x, y, z)

    def compute_surface_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> Mesh:
        return cast(Mesh, self.final_geometry).copy()


class BrepElement(Element):
    """A context-free element represented by a native COMPAS BRep.

    The class keeps the BRep representation intact. Surface meshes are created
    only when `surface_mesh` or `collision_mesh` is requested.

    Parameters
    ----------
    geometry
        The BRep in element-local coordinates.
    transformation
        The transformation from element-local to parent coordinates.
    features
        Features applied in order before model transformations and modifiers.
    material
        The element material.
    name
        The element name.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data["geometry"] = self.geometry
        return data

    def __init__(
        self,
        geometry: Brep,
        transformation: Optional[Transformation] = None,
        features: Optional[list[Feature]] = None,
        material: Optional[Material] = None,
        name: Optional[str] = None,
    ) -> None:
        if not isinstance(geometry, Brep):
            raise TypeError("BrepElement geometry should be a Brep.")
        super().__init__(geometry=geometry, transformation=transformation, features=features, material=material, name=name)

    @property
    def is_empty(self) -> bool:
        """bool: Whether the evaluated BRep has no topology."""
        return is_geometry_empty(self.final_geometry)

    def compute_base_geometry(self) -> Brep:
        geometry = self.geometry
        if not isinstance(geometry, Brep):
            raise TypeError("BrepElement geometry should be a Brep.")
        return geometry.copy()

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        if self.is_empty:
            raise ValueError("An empty element has no axis-aligned bounding box.")
        geometry = cast(Brep, self.final_geometry)
        return _inflated(geometry.aabb.copy(), inflate)

    def compute_obb(self, inflate: float = 1.0) -> Box:
        if self.is_empty:
            raise ValueError("An empty element has no oriented bounding box.")
        geometry = cast(Brep, self.final_geometry)
        return _inflated(geometry.obb.copy(), inflate)

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        if inflate != 1.0:
            raise NotImplementedError("Inflated collision meshes are not supported; inflate the broad-phase bounds instead.")
        return self.compute_surface_mesh()

    def compute_point(self) -> Point:
        geometry = cast(Brep, self.final_geometry)
        return geometry.centroid.copy()

    def compute_surface_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> Mesh:
        geometry = cast(Brep, self.final_geometry)
        return geometry.to_tessellation(
            linear_deflection=TOL.lineardeflection,
            angular_deflection=degrees(TOL.angulardeflection),
        ).to_mesh()


class PrimitiveElement(MeshElement):
    """A context-free element represented parametrically by a COMPAS shape.

    Primitive elements evaluate to a mesh. This makes collision, contact, and
    visualization dispatch deterministic without requiring a BRep backend.

    Parameters
    ----------
    primitive
        A COMPAS shape supporting conversion to a mesh.
    transformation
        The transformation from element-local to parent coordinates.
    features
        Mesh features applied in order before model transformations and
        modifiers.
    material
        The element material.
    name
        The element name.

    """

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.pop("geometry")
        data["primitive"] = self.primitive
        return data

    def __init__(
        self,
        primitive: Shape,
        transformation: Optional[Transformation] = None,
        features: Optional[list[Feature]] = None,
        material: Optional[Material] = None,
        name: Optional[str] = None,
    ) -> None:
        if not isinstance(primitive, Shape):
            raise TypeError("PrimitiveElement primitive should be a Shape.")
        self.primitive = primitive
        super().__init__(
            geometry=primitive.to_polygonal_surface().to_mesh(),
            transformation=transformation,
            features=features,
            material=material,
            name=name,
        )

    def compute_base_geometry(self) -> Mesh:
        self._geometry = self.primitive.to_polygonal_surface().to_mesh()
        return super().compute_base_geometry()
