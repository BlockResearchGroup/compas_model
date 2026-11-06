from importlib import import_module

from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Brep
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import Polygon
from compas_model.geometry import PlanarRegion


class Contact(Data):
    """Class representing a planar contact between two elements.

    Parameters
    ----------
    region
        The authoritative planar contact region. The region also provides the
        oriented contact frame.
    name
        A human-readable name.

    Warnings
    --------
    The definition of contact surfaces is under active development and may change frequently.

    """

    @property
    def __data__(self) -> dict:
        return {
            "name": self.name,
            "region": self.region,
        }

    def __init__(self, region: PlanarRegion, name: str | None = None) -> None:
        if not isinstance(region, PlanarRegion):
            raise TypeError("Contact region should be a PlanarRegion.")
        super().__init__(name=name)
        self._region = region
        self._mesh = None
        self._brep = None

    @property
    def region(self) -> PlanarRegion:
        """PlanarRegion: The authoritative planar contact geometry."""
        return self._region

    @property
    def polygon(self) -> Polygon:
        """Polygon: The exterior boundary of the contact region."""
        return self.region.exterior

    @property
    def geometry(self) -> PlanarRegion:
        """PlanarRegion: The complete contact region, including holes."""
        return self.region

    @property
    def points(self) -> list[Point]:
        return self.polygon.points

    @property
    def holes(self) -> list[Polygon]:
        """list[Polygon]: The interior boundaries of the contact region."""
        return self.region.holes

    @property
    def frame(self) -> Frame:
        """Frame: The oriented frame of the contact region."""
        return self.region.frame

    @property
    def mesh(self) -> Mesh:
        if self._mesh is None:
            self._mesh = self.region.to_mesh()
        return self._mesh

    @property
    def brep(self) -> Brep:
        """The contact region represented as a core COMPAS BRep.

        Raises
        ------
        ImportError
            If the optional COMPAS OCC backend is unavailable.

        """
        if self._brep is None:
            try:
                backend = import_module("compas_model.algorithms._occ")
            except ImportError as error:
                raise ImportError("Contact BRep conversion requires the optional COMPAS OCC backend.") from error
            self._brep = backend.brep_from_planar_region_occ(self.polygon, self.holes)
        return self._brep

    @property
    def size(self) -> float:
        return self.region.area
