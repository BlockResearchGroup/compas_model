from compas.scene import SceneObject


class ElementObject(SceneObject):
    def __init__(self, element):
        super(ElementObject, self).__init__(item=element)
        self.element = element
