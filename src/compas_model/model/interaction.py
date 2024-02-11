from compas.data import Data


class Interaction(Data):
    def __data__(self):
        return {"name": self.name, "value": self.value}

    def __init__(self, name=None, value=None):
        super().__init__(name=name)
        self.value = value
