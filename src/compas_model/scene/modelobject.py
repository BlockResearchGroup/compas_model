from typing import Optional

from compas.geometry import Transformation
from compas.scene import Group
from compas.scene import SceneObject
from compas_model.models import Model


class ModelObject(SceneObject):
    def __init__(
        self,
        show_elements: Optional[bool] = True,
        show_contacts: Optional[bool] = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.show_elements = show_elements
        self.show_contacts = show_contacts

        self._add_elements(**kwargs)

    def _add_elements(self, **kwargs) -> None:
        elements_group = self.add(Group(name="Elements", context=self.context))
        contacts_group = self.add(Group(name="Contacts", context=self.context))

        if self.show_elements:
            for element in self.model.tree.rootelements:
                element_kwargs = kwargs.copy()
                element_kwargs["item"] = element
                elements_group.add(**element_kwargs)

        if self.show_contacts:
            for contact in self.model.contacts():
                contact_kwargs = kwargs.copy()
                contact_kwargs["item"] = contact
                contacts_group.add(**contact_kwargs)

    @property
    def model(self) -> Model:
        return self.item

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
