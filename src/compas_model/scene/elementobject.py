from compas.scene import SceneObject


class ElementObject(SceneObject):
    def __init__(self, element, **kwargs):
        super(ElementObject, self).__init__(item=element, **kwargs)
        self.element = element
