from compas_model.interactions import Interaction


class Modifier(Interaction):
    def apply(self):
        raise NotImplementedError