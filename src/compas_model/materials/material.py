from compas.data import Data


class Material(Data):
    """Base class for all types of materials.

    Parameters
    ----------
    name : str, optional
        The name of the material.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(Material, self).__init__(name=name)

    def __repr__(self):
        return '{}(name="{}")'.format(self.__class__.__name__, self.name)
