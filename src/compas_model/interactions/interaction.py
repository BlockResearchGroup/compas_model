from typing import Optional

from compas.data import Data


class Interaction(Data):
    """Base class for all types of element-element interactions.

    an interaction between two elements is stored on an edge of the interaction graph
    an interaction can be a collision/intersection between two objects
        collisions/intersections are calculated by one of the collision/intersection algorithms
    an interaction can be an interface between two elements
        interfaces are calculated using one of the interface algorithms
        two interacting elements can have more than one interface
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
    def __data__(self) -> dict:
        return {"name": self.name}

    def __init__(self, name: Optional[str] = None) -> None:
        super().__init__(name=name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name="{self.name}")'

    def modify(self, targetgeometry, targetelement, sourceelement):
        """Apply modification to the target geometry e.g. slicing by plane, solid boolean.

        Parameters
        ----------
        targetgeometry : Brep or Mesh
            The geometry to be affected iteratively. The same geometry can be modified multiple times.
        targetelement : Element
            The element that is modified.
        sourceelement : Element
            The element that is transformed to the modelgeometry frame.
        """
        return targetgeometry
