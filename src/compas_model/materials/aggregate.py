from .material import Material


class Aggregates(Material):
    """Class representing a generic aggregate material.

    Parameters
    ----------
    name : str
        Name of the aggregate material.
    density : float
        Density of the material in [kg/m3].

    Attributes
    ----------
    name : str
        Name of the aggregate material.
    density : float
        Density of the material in [kg/m3].
    """

    TYPES = {
        "Sand": {
            "density": 1600,
        },
    }

    def __init__(self, name, density):
        super(Aggregates, self).__init__(name=name)
        self.density = density

    @property
    def rho(self):
        return self.density

    @classmethod
    def from_type(cls, aggregate_type):
        # type: (str) -> Aggregates
        """Construct an aggregate material from a predefined type.

        Parameters
        ----------
        aggregate_type : {'Sand'}
            The type of the aggregate.

        Returns
        -------
        :class:`Aggregates`
        """
        aggregate_type = aggregate_type.capitalize()
        if aggregate_type not in cls.TYPES:
            raise ValueError("Aggregate type not supported: {}".format(aggregate_type))
        params = cls.TYPES[aggregate_type]
        return cls(name=aggregate_type, **params)
