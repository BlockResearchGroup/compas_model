from compas.data import Data


class Interaction(Data):
    """Base class for all types of element-element interactions.

    Parameters
    ----------
    name : str, optional
        The name of the interaction.

    """

    @property
    def __data__(self):
        # type: () -> dict
        return {"name": self.name}

    def __init__(self, name=None):
        # type: (str | None) -> None
        super(Interaction, self).__init__(name=name)

    def __str__(self):
        return "<Interaction>"
