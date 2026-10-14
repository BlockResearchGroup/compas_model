from typing import Any

from compas.geometry import Transformation
from compas.scene import SceneObject
from compas_model.models import Model


class ModelObject(SceneObject):
    """Base scene object for a model.

    Parameters
    ----------
    add_elements
        If ``True``, recursively add scene objects for root model elements.
    **kwargs
        Additional keyword arguments for the base scene object.

    """

    def __init__(self, add_elements: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        if add_elements:
            for node in self.model.tree.root.children:
                element_kwargs = kwargs.copy()
                element_kwargs["item"] = node.element
                self.add(**element_kwargs)

    @property
    def model(self) -> Model:
        return self.item  # type: ignore

    @property
    def transformation(self) -> Transformation:
        return self._transformation

    @transformation.setter
    def transformation(self, transformation: Transformation) -> None:
        self._transformation = transformation

    def draw(self) -> None:
        """Draw the model."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all components of the model."""
        raise NotImplementedError
