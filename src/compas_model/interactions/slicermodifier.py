from compas.geometry import Plane  # noqa: F401

from compas_model.interactions import Interaction


class SlicerModifier(Interaction):
    """Base class for all types of element-element interactions.

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
        return {"name": self.name, "slice_plane": self.slice_plane}

    def __init__(self, slice_plane, name=None):
        # type: (Plane, str | None) -> None
        super(SlicerModifier, self).__init__(name=name)
        self.slice_plane = slice_plane  # Virtual geometry are stored in interaction.

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)

    def modify(self, targetgeometry, sourcegeometry):
        """Apply the interaction to the affected geometry.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        sourcegeometry : Brep or Mesh
            The geometry that is transformed to the modelgeometry frame.

        Returns
        -------
        Brep or Mesh
            The modified geometry.
        """

        from compas_model.algorithms.modifiers import slice  # or get rid of contact interactions in algorithms module

        return slice(targetgeometry, self.slice_plane)
