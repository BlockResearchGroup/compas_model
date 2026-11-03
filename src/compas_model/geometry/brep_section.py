from typing import Any
from typing import cast

from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polyline

from .mesh_section import reconstruct_planar_regions
from .planar_region import PlanarRegion
from .section import ClipElementResult
from .section import SectionClassification
from .section import SectionElementResult


def section_brep(
    brep: Brep,
    frame: Frame,
    source_guid: str,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
    curve_samples: int = 64,
) -> SectionElementResult:
    """Section a native COMPAS OCC BRep with an oriented plane.

    Parameters
    ----------
    brep
        The native OCC BRep to section. The input is not modified.
    frame
        The cutting-plane frame. Its Z axis points toward the front side.
    source_guid
        String representation of the source element GUID.
    tolerance
        Absolute distance used for classification and curve endpoint welding.
    minimum_area
        Minimum net area of returned polygonal section regions.
    curve_samples
        Number of samples used to convert every native section edge to a
        polyline for planar-region reconstruction.

    Returns
    -------
    SectionElementResult
        Section faces, outlines, and source-geometry classification.

    Raises
    ------
    ValueError
        If an option is invalid.

    Notes
    -----
    Plane intersection and solid trimming are native Open CASCADE operations.
    The returned ``PlanarRegion`` boundaries are polygonal approximations of
    the exact section curves controlled by ``curve_samples``.

    """
    _validate_options(tolerance, minimum_area, curve_samples)
    occ_brep = cast(Any, brep)
    plane = Plane.from_frame(frame)
    section = occ_brep.slice(plane)
    section_polylines = _section_polylines(section, curve_samples)
    regions, open_curves = reconstruct_planar_regions(
        section_polylines,
        frame,
        tolerance=tolerance,
        minimum_area=minimum_area,
    )

    distances = _brep_distances(occ_brep, frame)
    section_has_geometry = bool(section and (section.edges or section.points))
    classification = _classify_brep(distances, section_has_geometry, tolerance)
    return SectionElementResult(
        source_guid=source_guid,
        classification=classification,
        representation="brep",
        regions=regions,
        open_curves=open_curves,
    )


def clip_brep(
    brep: Brep,
    frame: Frame,
    source_guid: str,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
    cap: bool = True,
    curve_samples: int = 64,
) -> ClipElementResult:
    """Clip a native OCC BRep and retain everything behind the plane.

    Native OCC splitting always caps intersected BReps. Therefore ``cap=False``
    is unsupported when the BRep spans both half-spaces.

    Raises
    ------
    ValueError
        If `tolerance` or `minimum_area` is negative, or `curve_samples` is
        smaller than two.
    NotImplementedError
        If uncapped output is requested for an intersected BRep.

    Notes
    -----
    Exceptions from the active BRep backend are propagated unchanged unless a
    kernel operation is explicitly normalized to `RuntimeError`.

    """
    complete_section = section_brep(
        brep,
        frame,
        source_guid,
        tolerance=tolerance,
        minimum_area=0.0,
        curve_samples=curve_samples,
    )
    section = SectionElementResult(
        source_guid,
        cast(SectionClassification, complete_section.classification),
        "brep",
        regions=[region for region in complete_section.regions if region.area >= minimum_area],
        open_curves=complete_section.open_curves,
    )
    occ_brep = cast(Any, brep)
    distances = _brep_distances(occ_brep, frame)
    has_front = any(distance > tolerance for distance in distances)
    has_behind = any(distance < -tolerance for distance in distances)
    geometry = None

    if section.classification == "behind" or (section.classification == "intersecting" and has_behind and not has_front):
        geometry = occ_brep
    elif section.classification == "intersecting" and has_behind:
        if not cap:
            raise NotImplementedError("Retained intersected BRep geometry currently requires cap=True.")
        geometry = _trimmed(occ_brep, Plane.from_frame(frame))
    return ClipElementResult(section, geometry)


def intersection_brep_plane(
    brep: Brep,
    frame: Frame,
    tolerance: float = 1e-6,
    minimum_area: float = 0.0,
    curve_samples: int = 64,
) -> tuple[list[PlanarRegion], list[Polyline]]:
    """Intersect a native OCC BRep with a plane.

    Parameters
    ----------
    brep
        The native OCC BRep.
    frame
        The oriented cutting-plane frame.
    tolerance
        Absolute coplanarity and curve endpoint-welding tolerance.
    minimum_area
        Minimum net area of returned polygonal regions.
    curve_samples
        Samples per native section edge.

    Returns
    -------
    tuple[list[PlanarRegion], list[Polyline]]
        Polygonal closed regions and open intersection chains.

    Raises
    ------
    ValueError
        If `tolerance` or `minimum_area` is negative, or `curve_samples` is
        smaller than two.

    Notes
    -----
    Exceptions from the active BRep backend are propagated unchanged.

    """
    _validate_options(tolerance, minimum_area, curve_samples)
    occ_brep = cast(Any, brep)
    section = occ_brep.slice(Plane.from_frame(frame))
    return reconstruct_planar_regions(
        _section_polylines(section, curve_samples),
        frame,
        tolerance=tolerance,
        minimum_area=minimum_area,
    )


def _validate_options(tolerance: float, minimum_area: float, curve_samples: int) -> None:
    if tolerance < 0:
        raise ValueError("The tolerance should be greater than or equal to zero.")
    if minimum_area < 0:
        raise ValueError("The minimum area should be greater than or equal to zero.")
    if curve_samples < 2:
        raise ValueError("The number of curve samples should be at least two.")


def _section_polylines(section: Any, curve_samples: int) -> list[Polyline]:
    if section is None:
        return []
    return [edge.curve.to_polyline(n=curve_samples) for edge in section.edges]


def _classify_brep(
    distances: list[float],
    section_has_geometry: bool,
    tolerance: float,
) -> SectionClassification:
    if distances and all(abs(distance) <= tolerance for distance in distances):
        return "coplanar"
    if section_has_geometry:
        return "intersecting"
    if not distances:
        raise ValueError("The BRep has no points for half-space classification.")
    if all(distance > tolerance for distance in distances):
        return "front"
    if all(distance < -tolerance for distance in distances):
        return "behind"
    return "intersecting"


def _brep_distances(brep: Any, frame: Frame) -> list[float]:
    points = list(brep.points)
    try:
        for mesh in brep.to_meshes():
            for vertex in mesh.vertices():
                coordinates = mesh.vertex_coordinates(vertex)
                if coordinates is not None:
                    points.append(Point(*coordinates))
    except Exception as error:
        raise RuntimeError("Open CASCADE failed to tessellate the BRep for half-space classification.") from error
    return [(point - frame.point).dot(frame.zaxis) for point in points]


def _trimmed(brep: Any, plane: Plane) -> Brep:
    try:
        result = brep.trimmed(plane)
    except Exception as error:
        raise RuntimeError("Open CASCADE failed to trim the BRep with the section plane.") from error
    return result
