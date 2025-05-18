from typing import TYPE_CHECKING

from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Plane

from .modifier import Modifier

if TYPE_CHECKING:
    from compas_model.elements import Element


class TrimModifier(Modifier):
    def __init__(
        self,
        source: "Element",
        attributename: str,
        name: str | None = None,
    ) -> None:
        super().__init__(name)
        self.source = source
        self.attributename = attributename

        self._plane = None

    @property
    def plane(self) -> Plane:
        if not self._plane:
            self._plane = self.make_plane()
        return self._plane

    def make_plane(self) -> Plane:
        plane: Plane = getattr(self.source, self.attributename)
        plane = plane.copy()
        plane.normal.invert()
        return plane.transformed(self.source.transformation)

    def apply(self, target: Brep | Mesh) -> Brep | Mesh:
        if isinstance(target, Brep):
            return target.trimmed(self.plane)  # type: ignore
        raise Exception
