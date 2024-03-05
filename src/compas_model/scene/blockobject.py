from compas_model.scene import ElementObject


class BlockObject(ElementObject):
    """Scene object for drawing a block."""

    def __init__(self, block, **kwargs):
        super().__init__(element=block, **kwargs)
