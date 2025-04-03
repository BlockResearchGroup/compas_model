from compas_model.scene.modelobject import ModelObject as BaseModelObject
from compas_viewer.scene import Group
from compas_viewer.scene import ViewerSceneObject


class ModelObject(ViewerSceneObject, BaseModelObject):
    def add_elements(self, **kwargs) -> None:
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
