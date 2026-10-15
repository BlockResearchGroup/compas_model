from typing import Optional
from typing import cast

from compas.datastructures import Mesh
from compas.geometry import Box
from compas.geometry import Brep
from compas.geometry import Point
from compas.geometry import Shape
from compas.geometry import Transformation
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


def _join_meshes(meshes: list[Mesh]) -> Mesh:
    if not meshes:
        raise ValueError("The BRep did not produce any surface meshes.")
    result = meshes[0].copy()
    for mesh in meshes[1:]:
        result.join(mesh)
    return result


class MeshElement(Element):
    """A context-free element represented by a COMPAS mesh.

    Parameters
    ----------
    geometry
        The mesh in element-local coordinates.
    transformation
        The transformation from element-local to parent coordinates.
    features
        Features applied when explicitly requested.
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

    def compute_elementgeometry(self, include_features: bool = False) -> Mesh:
        geometry = self.geometry
        if not isinstance(geometry, Mesh):
            raise TypeError("MeshElement geometry should be a Mesh.")
        result = geometry.copy()
        if include_features:
            for feature in self.features:
                applied = feature.apply(result)
                if not isinstance(applied, Mesh):
                    raise TypeError("MeshElement features should return a Mesh.")
                result = applied
        return result

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        return _inflated(self.modelgeometry.aabb(), inflate)

    def compute_obb(self, inflate: float = 1.0) -> Box:
        return _inflated(self.modelgeometry.obb(), inflate)

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        if inflate != 1.0:
            raise NotImplementedError("Inflated collision meshes are not supported; inflate the broad-phase bounds instead.")
        return self.modelgeometry.copy()

    def compute_point(self) -> Point:
        return Point(*self.modelgeometry.centroid())

    def compute_surface_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> Mesh:
        return self.modelgeometry.copy()


class BrepElement(Element):
    """A context-free element represented by a native COMPAS BRep.

    The class keeps the BRep representation intact. Surface meshes are created
    only when :attr:`surface_mesh` or :attr:`collision_mesh` is requested.

    Parameters
    ----------
    geometry
        The BRep in element-local coordinates.
    transformation
        The transformation from element-local to parent coordinates.
    features
        Features applied when explicitly requested.
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

    def compute_elementgeometry(self, include_features: bool = False) -> Brep:
        geometry = self.geometry
        if not isinstance(geometry, Brep):
            raise TypeError("BrepElement geometry should be a Brep.")
        result = geometry.copy()
        if include_features:
            for feature in self.features:
                applied = feature.apply(result)
                if not isinstance(applied, Brep):
                    raise TypeError("BrepElement features should return a Brep.")
                result = applied
        return result

    def compute_aabb(self, inflate: float = 1.0) -> Box:
        geometry = cast(Brep, self.modelgeometry)
        return _inflated(geometry.aabb.copy(), inflate)

    def compute_obb(self, inflate: float = 1.0) -> Box:
        geometry = cast(Brep, self.modelgeometry)
        return _inflated(geometry.obb.copy(), inflate)

    def compute_collision_mesh(self, inflate: float = 1.0) -> Mesh:
        if inflate != 1.0:
            raise NotImplementedError("Inflated collision meshes are not supported; inflate the broad-phase bounds instead.")
        return self.compute_surface_mesh()

    def compute_point(self) -> Point:
        geometry = cast(Brep, self.modelgeometry)
        return geometry.centroid.copy()

    def compute_surface_mesh(self, meshsize_min: Optional[float] = None, meshsize_max: Optional[float] = None) -> Mesh:
        geometry = cast(Brep, self.modelgeometry)
        return _join_meshes(geometry.to_meshes())


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
        Mesh features applied when explicitly requested.
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
        super().__init__(geometry=primitive.to_mesh(), transformation=transformation, features=features, material=material, name=name)

    def compute_elementgeometry(self, include_features: bool = False) -> Mesh:
        self._geometry = self.primitive.to_mesh()
        return super().compute_elementgeometry(include_features=include_features)
