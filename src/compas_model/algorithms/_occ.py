from compas_occ.brep import OCCBrep
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.Precision import precision


def is_brep_brep_collision_occ(
    brep_a: OCCBrep,
    brep_b: OCCBrep,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Test two COMPAS OCC BReps for collision."""
    if include_touching:
        query = BRepExtrema_DistShapeShape(brep_a.occ_shape, brep_b.occ_shape)
        query.Perform()
        if not query.IsDone():
            raise RuntimeError("Open CASCADE failed to compute the distance between the BReps.")
        return query.Value() <= max(tolerance, precision.Confusion())

    if tolerance > 0:
        raise NotImplementedError("Precise BRep collision cannot combine positive tolerance with excluded touching.")
    if not brep_a.is_solid or not brep_b.is_solid:
        raise NotImplementedError("Precise BRep collision excluding touching requires two solids.")

    try:
        common = brep_a.boolean_intersection(brep_b)
        return common.is_solid and common.volume > 0.0
    except Exception as error:
        raise RuntimeError("Open CASCADE failed to compute the common volume of the BReps.") from error
