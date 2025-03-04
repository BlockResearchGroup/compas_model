from typing import Optional

from compas.geometry import Transformation
from compas.scene import SceneObject
from compas_model.models import Model


class ModelObject(SceneObject):
    def __init__(
        self,
        show_elements: Optional[bool] = True,
        show_contacts: Optional[bool] = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._model = kwargs.get("item", None)

        self.show_elements = show_elements
        self.show_contacts = show_contacts

        for element in self.model.elements():
            element_kwargs = kwargs.copy()
            element_kwargs["item"] = element
            self.add(**element_kwargs)

        # for contact in self.model.contacts():
        #     self.add(**kwargs)

    @property
    def model(self) -> Model:
        return self._model

    @model.setter
    def model(self, model: Model) -> None:
        self._model = model
        self._transformation = None

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
