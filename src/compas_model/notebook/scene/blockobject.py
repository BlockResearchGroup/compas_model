from compas_notebook.scene import ThreeMeshObject


class ThreeBlockObject(ThreeMeshObject):

    def __init__(self, element, *args, **kwargs):
        super().__init__(mesh=element.geometry, **kwargs)
