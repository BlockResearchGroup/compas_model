from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.Precision import precision

from compas.geometry import Brep
from compas.geometry import Polygon


def is_brep_brep_collision_occ(
    brep_a: Brep,
    brep_b: Brep,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Test two COMPAS BReps for collision."""
    if include_touching:
        query = BRepExtrema_DistShapeShape(brep_a.native_brep, brep_b.native_brep)  # type: ignore[reportAttributeAccessIssue]
        query.Perform()
        if not query.IsDone():
            raise RuntimeError("Open CASCADE failed to compute the distance between the BReps.")
        return query.Value() <= max(tolerance, precision.Confusion())

    if tolerance > 0:
        raise NotImplementedError("Precise BRep collision cannot combine positive tolerance with excluded touching.")
    if not brep_a.is_solid or not brep_b.is_solid:
        raise NotImplementedError("Precise BRep collision excluding touching requires two solids.")

    try:
        common = Brep.from_boolean_intersection(brep_a, brep_b)
        return common.is_solid and common.volume > 0.0
    except Exception as error:
        raise RuntimeError("Open CASCADE failed to compute the common volume of the BReps.") from error


def brep_from_planar_region_occ(exterior: Polygon, holes: list[Polygon]) -> Brep:
    """Construct a planar BRep region through the optional OCC backend.

    The public COMPAS BRep facade owns the final BRep construction. Direct OCC
    access is limited to face and loop construction because core COMPAS does
    not yet expose backend-neutral factories for those topology objects.

    """
    if not holes:
        return Brep.from_polygons([exterior])

    from compas_occ.brep import OCCBrepFace
    from compas_occ.brep import OCCBrepLoop

    loops = [OCCBrepLoop.from_polygon(hole) for hole in holes]
    face = OCCBrepFace.from_polygon(exterior, holes=loops)
    return Brep.from_brepfaces([face])
