from importlib import import_module
from typing import Any

from compas.geometry import Brep


def _backend() -> dict[str, Any]:
    try:
        brep_module = import_module("compas_occ.brep")
        check_module = import_module("OCC.Core.BRepCheck")
        extrema_module = import_module("OCC.Core.BRepExtrema")
        precision_module = import_module("OCC.Core.Precision")
    except ImportError as error:
        raise ImportError(
            "Precise BRep collision detection requires the optional 'compas_occ' backend. Install compas_model with the 'brep' extra or install compas_occ from conda-forge."
        ) from error
    return {
        "brep_type": brep_module.OCCBrep,
        "analyzer_type": check_module.BRepCheck_Analyzer,
        "distance_type": extrema_module.BRepExtrema_DistShapeShape,
        "confusion": precision_module.precision.Confusion,
    }


def _native_shape(brep: Brep) -> Any:
    backend = _backend()
    if not isinstance(brep, backend["brep_type"]):
        raise TypeError("Precise BRep collision detection currently requires two COMPAS OCC BReps.")
    occ_brep: Any = brep
    try:
        shape = occ_brep.occ_shape
    except AttributeError as error:
        raise ValueError("The BRep has no native OCC shape.") from error
    if shape.IsNull():
        raise ValueError("The BRep has an empty native OCC shape.")
    if not backend["analyzer_type"](shape).IsValid():
        raise ValueError("The BRep native OCC shape is invalid.")
    return shape


def is_brep_brep_collision_occ(
    brep_a: Brep,
    brep_b: Brep,
    tolerance: float = 0.0,
    include_touching: bool = True,
) -> bool:
    """Test two COMPAS OCC BReps for collision."""
    backend = _backend()
    shape_a = _native_shape(brep_a)
    shape_b = _native_shape(brep_b)

    if include_touching:
        query = backend["distance_type"](shape_a, shape_b)
        query.Perform()
        if not query.IsDone():
            raise RuntimeError("Open CASCADE failed to compute the distance between the BReps.")
        return query.Value() <= max(tolerance, backend["confusion"]())

    if tolerance > 0:
        raise NotImplementedError("Precise BRep collision cannot combine positive tolerance with excluded touching.")
    occ_brep_a: Any = brep_a
    occ_brep_b: Any = brep_b
    if not occ_brep_a.is_solid or not occ_brep_b.is_solid:
        raise NotImplementedError("Precise BRep collision excluding touching requires two solids.")

    try:
        common = occ_brep_a.boolean_intersection(occ_brep_b)
        return common.is_solid and common.volume > 0.0
    except Exception as error:
        raise RuntimeError("Open CASCADE failed to compute the common volume of the BReps.") from error
