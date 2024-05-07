from compas.geometry import Frame  # noqa: F401
from compas.geometry import Point  # noqa: F401
from compas.geometry import Polygon  # noqa: F401

from .interaction import Interaction


class ContactInteraction(Interaction):
    """Class representing an interaction between two elements through surface-to-surface contact.

    Parameters
    ----------
    geometry : :class:`compas.geometry.Polygon`
        The polygon representing the geometry over which the interaction takes place.
    name : str, optional
        The name of the interaction.

    Attributes
    ----------

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "geometry": self.geometry,
            "name": self.name,
        }

    def __init__(self, geometry, name=None):
        # type: (Polygon, str | None) -> None
        super(ContactInteraction, self).__init__(name)
        self._size = 0
        self.geometry = geometry

    @property
    def points(self):
        # type: () -> list[Point]
        return self.geometry.points

    @property
    def frame(self):
        # type: () -> Frame
        return self.geometry.frame

    @property
    def size(self):
        # type: () -> float
        return self.geometry.area


class HardContactInteraction(ContactInteraction):
    """Class representing an interaction between two elements through a hard, compression-only, non-deformable contact."""

    def __init__(self, geometry, name=None):
        # type: (Polygon, str | None) -> None
        super(HardContactInteraction, self).__init__(geometry, name=name)


class SoftContactInteraction(ContactInteraction):
    def __init__(self, geometry, name=None):
        # type: (Polygon, str | None) -> None
        super(SoftContactInteraction, self).__init__(geometry, name=name)


class StickyContactInteraction(ContactInteraction):
    def __init__(self, geometry, name=None):
        # type: (Polygon, str | None) -> None
        super(StickyContactInteraction, self).__init__(geometry, name=name)
