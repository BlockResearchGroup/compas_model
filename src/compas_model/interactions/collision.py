from compas.geometry import Plane  # noqa: F401

from .interaction import Interaction


class Collision(Interaction):
    """Perform boolean difference on the target element.

    an interaction can be a modifier applied to the modelgeometry of an element
        the modifier is defined by a source element
        the modifier is applied to a target element
        source and target correspond to the direction of the interaction edge
        examples: SliceModifier, BooleanModifier, ...


    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(Collision, self).__init__(name=name)

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def collide(self, targetgeometry, sourcegeometry):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : Brep or Mesh
            The geometry that is transformed to the modelgeometry frame.

        Returns
        -------
        Boolean
            True if two elements collide, False otherwise.
        """
        return False
