from typing import TYPE_CHECKING

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas_model.geometry import is_geometry_empty

from .modifier import Modifier

if TYPE_CHECKING:
    from compas_model.elements import Element


class BrepDifferenceModifier(Modifier):
    """Subtract a source element's evaluated BRep from a target BRep.

    The source geometry is evaluated in model coordinates, including its own
    features and modifiers. The target geometry is the result of the target's
    preceding evaluation stages and modifier records.

    """

    def apply(self, source: "Element", target_geometry: Brep | Mesh) -> Brep:
        """Subtract the source geometry from the target geometry.

        Parameters
        ----------
        source
            Element providing the cutting BRep.
        target_geometry
            BRep to cut.

        Returns
        -------
        Brep
            Boolean difference returned by the active COMPAS BRep backend.

        Raises
        ------
        TypeError
            If either evaluated geometry is not a BRep or the backend returns
            a different representation.

        Notes
        -----
        Empty BReps and backend-specific failures are returned or propagated
        unchanged. No Mesh conversion is attempted.

        """
        if not isinstance(target_geometry, Brep):
            raise TypeError("BrepDifferenceModifier target geometry should be a BRep.")

        source_geometry = source.final_geometry
        if not isinstance(source_geometry, Brep):
            raise TypeError("BrepDifferenceModifier source geometry should be a BRep.")
        if is_geometry_empty(target_geometry) or is_geometry_empty(source_geometry):
            return target_geometry.copy()

        result = Brep.from_boolean_difference(target_geometry, source_geometry)
        if not isinstance(result, Brep):
            raise TypeError("The BRep backend should return a BRep for a Boolean difference.")
        return result
