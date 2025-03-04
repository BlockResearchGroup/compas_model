from compas_model.elements import Element
from .elementobject import ElementObject
from compas_viewer.scene import MeshObject


class ViewerElementObject(MeshObject, ElementObject):

    def __init__(self, item: Element = None, **kwargs):
        super().__init__(item=item.modelgeometry, **kwargs)
