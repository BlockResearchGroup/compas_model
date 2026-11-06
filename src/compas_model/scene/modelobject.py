from typing import Any

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
            root = self.model.tree.root
            if root is None:
                raise RuntimeError("The model hierarchy has no root node.")
            for node in root.children:
                element_kwargs = kwargs.copy()
                element_kwargs["item"] = node.element
                self.add(**element_kwargs)

    @property
    def model(self) -> Model:
        return self.item  # type: ignore

    def draw(self) -> list[object]:
        """Draw the model."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all components of the model."""
        raise NotImplementedError
