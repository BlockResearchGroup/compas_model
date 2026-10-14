from collections.abc import Iterable
from typing import Literal

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import Transformation

from .planar_region import PlanarRegion

SectionClassification = Literal["front", "behind", "intersecting", "coplanar"]
SectionRepresentation = Literal["mesh", "brep"]

SECTION_CLASSIFICATIONS = frozenset({"front", "behind", "intersecting", "coplanar"})
SECTION_REPRESENTATIONS = frozenset({"mesh", "brep"})


class SectionElementResult(Data):
    """Section geometry associated with one source element.

    Parameters
    ----------
    source_guid
        String representation of the source element GUID.
    classification
        Position of the source geometry relative to the cutting plane.
    representation
        Geometry representation used for sectioning.
    regions
        Closed planar section faces.
    open_curves
        Open intersection chains that could not form regions.
    name
        A human-readable name.

    Raises
    ------
    ValueError
        If the classification or representation is unsupported.

    """

    @property
    def __data__(self) -> dict:
        return {
            "source_guid": self.source_guid,
            "classification": self.classification,
            "representation": self.representation,
            "regions": self.regions,
            "open_curves": self.open_curves,
            "name": self.name,
        }

    def __init__(
        self,
        source_guid: str,
        classification: SectionClassification,
        representation: SectionRepresentation,
        regions: Iterable[PlanarRegion] | None = None,
        open_curves: Iterable[Polyline] | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        if classification not in SECTION_CLASSIFICATIONS:
            raise ValueError(f"Unsupported section classification: {classification!r}.")
        if representation not in SECTION_REPRESENTATIONS:
            raise ValueError(f"Unsupported section representation: {representation!r}.")
        self.source_guid = str(source_guid)
        self.classification = classification
        self.representation = representation
        self.regions = [region.copy() for region in regions or []]
        self.open_curves = [curve.copy() for curve in open_curves or []]

    @property
    def outlines(self) -> list[Polyline]:
        """list[Polyline]: Closed region boundaries followed by open curves."""
        outlines = []
        for region in self.regions:
            for polygon in [region.exterior, *region.holes]:
                outlines.append(Polyline([*polygon.points, polygon.points[0]]))
        return [*outlines, *self.open_curves]

    def transform(self, transformation: Transformation) -> None:
        """Transform all section geometry stored in the result."""
        for region in self.regions:
            region.transform(transformation)
        for curve in self.open_curves:
            curve.transform(transformation)

    def transformed(self, transformation: Transformation) -> "SectionElementResult":
        """Return a transformed copy of the result."""
        result = self.copy()
        result.transform(transformation)
        return result


class SectionResult(Data):
    """Ordered section geometry from model elements and an oriented plane."""

    @property
    def __data__(self) -> dict:
        return {
            "frame": self.frame,
            "elements": self.elements,
            "tolerance": self.tolerance,
            "name": self.name,
        }

    def __init__(
        self,
        frame: Frame,
        elements: Iterable[SectionElementResult] | None = None,
        tolerance: float = 1e-6,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        if tolerance < 0:
            raise ValueError("The section tolerance should be greater than or equal to zero.")
        self.frame = frame.copy()
        self.elements = [element.copy() for element in elements or []]
        self.tolerance = float(tolerance)
        self._validate_section_geometry()

    def signed_distance(self, point: Point) -> float:
        """Compute signed distance along the cutting frame's Z axis."""
        return (point - self.frame.point).dot(self.frame.zaxis)

    def classify_point(self, point: Point) -> Literal["front", "behind", "coplanar"]:
        """Classify a point relative to the cutting plane."""
        distance = self.signed_distance(point)
        if distance > self.tolerance:
            return "front"
        if distance < -self.tolerance:
            return "behind"
        return "coplanar"

    def _validate_section_geometry(self) -> None:
        for element in self.elements:
            points = [
                *(point for region in element.regions for point in region.points),
                *(point for curve in element.open_curves for point in curve.points),
            ]
            if any(abs(self.signed_distance(point)) > self.tolerance for point in points):
                raise ValueError("Section regions and open curves should lie on the cutting plane.")

    def by_classification(self, classification: SectionClassification) -> list[SectionElementResult]:
        """Return element records with a specific classification."""
        if classification not in SECTION_CLASSIFICATIONS:
            raise ValueError(f"Unsupported section classification: {classification!r}.")
        return [element for element in self.elements if element.classification == classification]

    @property
    def front(self) -> list[SectionElementResult]:
        """list[SectionElementResult]: Records entirely in front of the plane."""
        return self.by_classification("front")

    @property
    def behind(self) -> list[SectionElementResult]:
        """list[SectionElementResult]: Records entirely behind the plane."""
        return self.by_classification("behind")

    @property
    def intersecting(self) -> list[SectionElementResult]:
        """list[SectionElementResult]: Records intersecting the plane."""
        return self.by_classification("intersecting")

    @property
    def coplanar(self) -> list[SectionElementResult]:
        """list[SectionElementResult]: Records coplanar with the plane."""
        return self.by_classification("coplanar")

    @property
    def regions(self) -> list[PlanarRegion]:
        """list[PlanarRegion]: All closed section faces in element order."""
        return [region for element in self.elements for region in element.regions]

    @property
    def outlines(self) -> list[Polyline]:
        """list[Polyline]: All closed boundaries and open curves."""
        return [outline for element in self.elements for outline in element.outlines]

    @property
    def open_curves(self) -> list[Polyline]:
        """list[Polyline]: All open section curves in element order."""
        return [curve for element in self.elements for curve in element.open_curves]

    def transform(self, transformation: Transformation) -> None:
        """Transform the cutting frame and all section geometry."""
        self.frame.transform(transformation)
        for element in self.elements:
            element.transform(transformation)

    def transformed(self, transformation: Transformation) -> "SectionResult":
        """Return a transformed copy of the complete section result."""
        result = self.copy()
        result.transform(transformation)
        return result


class ClipElementResult(Data):
    """Negative-half-space geometry paired with its section record."""

    @property
    def __data__(self) -> dict:
        return {"section": self.section, "geometry": self.geometry, "name": self.name}

    def __init__(
        self,
        section: SectionElementResult,
        geometry: Mesh | Brep | None = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        expected = Mesh if section.representation == "mesh" else Brep
        if geometry is not None and not isinstance(geometry, expected):
            raise TypeError(f"Clip geometry should match the {section.representation!r} representation.")
        self.section = section.copy()
        self.geometry = geometry.copy() if geometry is not None else None

    @property
    def source_guid(self) -> str:
        """str: GUID of the source element."""
        return self.section.source_guid

    @property
    def classification(self) -> SectionClassification:
        """SectionClassification: Position of the source geometry."""
        return self.section.classification

    def transform(self, transformation: Transformation) -> None:
        """Transform the section and retained geometry."""
        self.section.transform(transformation)
        if self.geometry is not None:
            self.geometry.transform(transformation)

    def transformed(self, transformation: Transformation) -> "ClipElementResult":
        """Return a transformed copy of the clip result."""
        result = self.copy()
        result.transform(transformation)
        return result


class ClipResult(Data):
    """Ordered negative-half-space geometry and associated section results."""

    @property
    def __data__(self) -> dict:
        return {
            "frame": self.frame,
            "elements": self.elements,
            "tolerance": self.tolerance,
            "cap": self.cap,
            "name": self.name,
        }

    def __init__(
        self,
        frame: Frame,
        elements: Iterable[ClipElementResult] | None = None,
        tolerance: float = 1e-6,
        cap: bool = True,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        if tolerance < 0:
            raise ValueError("The clip tolerance should be greater than or equal to zero.")
        self.frame = frame.copy()
        self.elements = [element.copy() for element in elements or []]
        self.tolerance = float(tolerance)
        self.cap = bool(cap)
        SectionResult(self.frame, [element.section for element in self.elements], tolerance=self.tolerance)

    @property
    def section(self) -> SectionResult:
        """SectionResult: The section geometry associated with this clip."""
        return SectionResult(self.frame, [element.section for element in self.elements], tolerance=self.tolerance)

    @property
    def geometry(self) -> list[Mesh | Brep]:
        """list[Mesh or Brep]: Retained geometry in element order."""
        return [element.geometry for element in self.elements if element.geometry is not None]

    def transform(self, transformation: Transformation) -> None:
        """Transform the cutting frame and every element clip result."""
        self.frame.transform(transformation)
        for element in self.elements:
            element.transform(transformation)

    def transformed(self, transformation: Transformation) -> "ClipResult":
        """Return a transformed copy of the complete clip result."""
        result = self.copy()
        result.transform(transformation)
        return result
