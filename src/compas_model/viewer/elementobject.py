from compas_model.elements import Element
from compas_model.scene.elementobject import ElementObject as BaseElementObject
from compas_viewer.scene import MeshObject

# TODO: Deal with BRep


class ElementObject(MeshObject, BaseElementObject):
    def __init__(self, item: Element = None, **kwargs):
        super().__init__(item=item.modelgeometry, **kwargs)
        self.name = item.name
