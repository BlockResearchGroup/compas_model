from typing import Optional

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
    points
        The points defining the exterior contact polygon. Required only when
        ``region`` is omitted.
    region
        The authoritative planar contact region.
    frame
        The local coordinate system of the contact.
    size
        Deprecated compatibility parameter. Contact size is derived from the
        net area of ``region``.
    mesh
        The mesh representation of the contact surface.
    holes
        Holes in the contact polygon.
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
            "mesh": self._mesh,
        }

    def __init__(
        self,
        points: Optional[list[Point]] = None,
        region: Optional[PlanarRegion] = None,
        frame: Optional[Frame] = None,
        size: Optional[float] = None,
        mesh: Optional[Mesh] = None,
        holes: Optional[list[Polygon]] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name)

        if region is None:
            if points is None:
                raise ValueError("Contact requires a planar region or exterior points.")
            region = PlanarRegion(Polygon(points), holes=holes, frame=frame)
        self._region = region
        self._mesh = mesh
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
        return self.region.frame

    @property
    def mesh(self) -> Mesh:
        if self._mesh is None:
            self._mesh = self.region.to_mesh()
        return self._mesh

    @property
    def brep(self) -> Brep:
        if self._brep is None:
            if self.holes:
                from compas_occ.brep import OCCBrepFace
                from compas_occ.brep import OCCBrepLoop

                face = OCCBrepFace.from_polygon(self.polygon)
                loops = []
                for hole in self.holes:
                    loop = OCCBrepLoop.from_polygon(hole)
                    loops.append(loop)
                face.add_loops(loops)
                self._brep = Brep.from_brepfaces([face])
            else:
                self._brep = Brep.from_polygons([self.polygon])
        return self._brep

    @property
    def size(self) -> float:
        return self.region.area
