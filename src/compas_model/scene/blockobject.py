from compas.scene import SceneObject


class BlockObject(SceneObject):
    def __init__(self, element, **kwargs):
        super(BlockObject, self).__init__(item=element, **kwargs)
        self.element = element
