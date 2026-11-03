from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.Precision import precision

from compas.geometry import Brep


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
