from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from math import sqrt
from typing import Literal

import numpy as np

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.elements import Element
from compas_model.elements import GeometryStage
from compas_model.geometry import is_geometry_empty
from compas_model.models import ModelUnit

from .rendergeometry import RenderGeometry
from .rendergeometry import render_geometry_from_brep
from .rendergeometry import render_geometry_from_mesh

RenderQuality = Literal["draft", "standard", "high"]
RENDER_QUALITIES = frozenset({"draft", "standard", "high"})
GEOMETRY_STAGES = frozenset({"base", "local", "model", "final"})
METERS_PER_MODEL_UNIT: dict[ModelUnit, float] = {"M": 1.0, "MM": 1e-3}
QUALITY_DEFLECTIONS: dict[RenderQuality, tuple[float, float, float, float]] = {
    "draft": (1e-2, 1e-4, 2e-2, 0.20),
    "standard": (1e-3, 1e-5, 5e-3, 0.10),
    "high": (1e-4, 1e-6, 1e-3, 0.05),
}
MESH_TOLERANCE_METERS = 1e-9


@dataclass(frozen=True, slots=True)
class RenderSettings:
    """Settings that affect generated render geometry.

    Parameters
    ----------
    unit
        Length unit used by coordinate values.
    quality
        Named scale-aware visual approximation quality.
    geometry_stage
        Cached element geometry stage to render.
    mesh_tolerance
        Optional cleanup tolerance in model units. If omitted, a physically
        equivalent default is derived from ``unit``.
    linear_deflection
        Optional BRep tessellation linear deflection.
    angular_deflection
        Optional BRep tessellation angular deflection in radians.

    """

    unit: ModelUnit = "M"
    quality: RenderQuality = "standard"
    geometry_stage: GeometryStage = "final"
    mesh_tolerance: float | None = None
    linear_deflection: float | None = None
    angular_deflection: float | None = None

    def __post_init__(self) -> None:
        if self.unit not in METERS_PER_MODEL_UNIT:
            raise ValueError(f"Unsupported render length unit: {self.unit!r}.")
        if self.quality not in RENDER_QUALITIES:
            raise ValueError(f"Unsupported render quality: {self.quality!r}.")
        if self.geometry_stage not in GEOMETRY_STAGES:
            raise ValueError(f"Unsupported geometry stage: {self.geometry_stage!r}.")
        if self.mesh_tolerance is not None and self.mesh_tolerance < 0:
            raise ValueError("The mesh render tolerance should be greater than or equal to zero.")
        if self.linear_deflection is not None and self.linear_deflection <= 0:
            raise ValueError("The BRep linear deflection should be greater than zero.")
        if self.angular_deflection is not None and self.angular_deflection <= 0:
            raise ValueError("The BRep angular deflection should be greater than zero.")

    @property
    def effective_mesh_tolerance(self) -> float:
        """float: Mesh cleanup tolerance expressed in model units."""
        if self.mesh_tolerance is not None:
            return self.mesh_tolerance
        return MESH_TOLERANCE_METERS / METERS_PER_MODEL_UNIT[self.unit]

    def effective_linear_deflection(self, characteristic_length: float) -> float:
        """Compute BRep linear deflection for an object size.

        Parameters
        ----------
        characteristic_length
            Object bounding-box diagonal expressed in model units.

        Returns
        -------
        float
            Scale-aware linear deflection expressed in model units.

        Raises
        ------
        ValueError
            If the characteristic length is negative or non-finite.

        """
        if characteristic_length < 0 or not isfinite(characteristic_length):
            raise ValueError("The characteristic length should be finite and greater than or equal to zero.")
        if self.linear_deflection is not None:
            return self.linear_deflection
        relative, minimum_m, maximum_m, _ = QUALITY_DEFLECTIONS[self.quality]
        scale = METERS_PER_MODEL_UNIT[self.unit]
        return min(max(relative * characteristic_length, minimum_m / scale), maximum_m / scale)

    @property
    def effective_angular_deflection(self) -> float:
        """float: BRep angular deflection in radians."""
        if self.angular_deflection is not None:
            return self.angular_deflection
        _, _, _, angular_deflection = QUALITY_DEFLECTIONS[self.quality]
        return angular_deflection


RenderGeometryBuilder = Callable[[Element, RenderSettings], RenderGeometry]


@dataclass(frozen=True, slots=True)
class _RenderCacheEntry:
    element_identity: int
    geometry_revision: int
    settings: RenderSettings
    geometry: RenderGeometry


class RenderGeometryCache:
    """Revision-aware cache of element render geometry.

    Parameters
    ----------
    builder
        Optional render-geometry builder. The default dispatches Mesh and BRep
        representations without converting between them.

    Notes
    -----
    Entries are keyed by element GUID and additionally verify object identity,
    geometry revision, and render settings. The cache owns CPU-side arrays; GPU
    buffer lifetime remains the responsibility of COMPAS Viewer.

    """

    def __init__(self, builder: RenderGeometryBuilder | None = None) -> None:
        self._builder = builder or _build_render_geometry
        self._entries: dict[str, _RenderCacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def hits(self) -> int:
        """int: Number of render-geometry cache hits."""
        return self._hits

    @property
    def misses(self) -> int:
        """int: Number of render-geometry cache misses."""
        return self._misses

    def get(self, element: Element, settings: RenderSettings | None = None) -> RenderGeometry:
        """Return current render geometry for an element.

        Parameters
        ----------
        element
            Element whose final geometry should be rendered.
        settings
            Tessellation and triangulation settings.

        Returns
        -------
        RenderGeometry
            Cached or newly generated render geometry.

        Raises
        ------
        TypeError
            If the element has no supported Mesh or BRep representation.

        """
        settings = settings or RenderSettings()
        guid = str(element.guid)
        entry = self._entries.get(guid)
        if entry is not None and entry.element_identity == id(element) and entry.geometry_revision == element.geometry_revision and entry.settings == settings:
            self._hits += 1
            return entry.geometry

        geometry = self._builder(element, settings)
        self._entries[guid] = _RenderCacheEntry(
            element_identity=id(element),
            geometry_revision=element.geometry_revision,
            settings=settings,
            geometry=geometry,
        )
        self._misses += 1
        return geometry

    def invalidate(self, element: Element | None = None) -> None:
        """Invalidate one element entry or clear the entire cache.

        Parameters
        ----------
        element
            Element to invalidate. If omitted, all entries are removed.

        """
        if element is None:
            self._entries.clear()
        else:
            self._entries.pop(str(element.guid), None)


def _build_render_geometry(element: Element, settings: RenderSettings) -> RenderGeometry:
    geometry = element.geometry_at(settings.geometry_stage)
    if is_geometry_empty(geometry):
        representation = "mesh" if isinstance(geometry, Mesh) else "brep"
        return RenderGeometry(
            vertices=np.empty((0, 3), dtype=np.float64),
            triangles=np.empty((0, 3), dtype=np.int32),
            line_vertices=np.empty((0, 3), dtype=np.float64),
            point_vertices=np.empty((0, 3), dtype=np.float64),
            representation=representation,
        )
    if isinstance(geometry, Mesh):
        return render_geometry_from_mesh(geometry, tolerance=settings.effective_mesh_tolerance)
    if isinstance(geometry, Brep):
        return render_geometry_from_brep(
            geometry,
            linear_deflection=settings.effective_linear_deflection(_characteristic_length(geometry)),
            angular_deflection=settings.effective_angular_deflection,
        )
    raise TypeError("Element render geometry requires a Mesh or BRep representation.")


def _characteristic_length(geometry: Mesh | Brep) -> float:
    """Return the origin-independent diagonal length of a geometry AABB."""
    box = geometry.aabb
    return sqrt(box.xsize**2 + box.ysize**2 + box.zsize**2)
