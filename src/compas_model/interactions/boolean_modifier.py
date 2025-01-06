from compas.geometry import Plane  # noqa: F401

from .interaction import Interaction


class BooleanModifier(Interaction):
    """Perform boolean difference on the target element.

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
        super(BooleanModifier, self).__init__(name=name)

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def modify(self, targetgeometry, sourcegeometry):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : Brep or Mesh
            The geometry to be used as the modifier.
        """
        from compas_model.algorithms.modifiers import boolean_difference  # Local import is needed otherwise, remove contact interactions in algorithms module.

        return boolean_difference(targetgeometry, sourcegeometry)
