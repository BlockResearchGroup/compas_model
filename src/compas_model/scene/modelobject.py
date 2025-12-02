from compas.geometry import Transformation
from compas.scene import SceneObject
from compas_model.models import Model


class ModelObject(SceneObject):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        for element in self.model.tree.rootelements:  # type: ignore
            element_kwargs = kwargs.copy()
            element_kwargs["item"] = element
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
        """draw the model.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all components of the model.

        Returns
        -------
        None

        """
        raise NotImplementedError
