from .material import Material


class Timber(Material):
    @property
    def __data__(self):
        # type: () -> dict
        data = super(Timber, self).__data__
        data.update({})
        return data

    def __init__(self, name=None):
        super(Timber, self).__init__(name=name)
from .material import Material


class Timber(Material):
    """Class representing a generic timber material.

    Parameters
    ----------
    fmk : float
        Characteristic bending strength in [MPa].
    fmk_tension : float, optional
        Characteristic tensile strength in [MPa].
        If not provided, `fmk_tension = 0.5 * fmk` is used.
    E0mean : float, optional
        Mean modulus of elasticity parallel to grain in [GPa].
        If not provided, `E0mean = 10.0` is used.
    density : float, optional
        Density of the material in [kg/m3].
        If not provided, 500 kg/m3 is used.
    poisson : float, optional
        Poisson's ratio.
        If not provided, `poisson = 0.4` is used.
    name : str, optional
        Name of the material.

    Attributes
    ----------
    fmk : float
        Characteristic bending strength in [MPa].
    fmk_tension : float
        Characteristic tensile strength in [MPa].
    E0mean : float
        Mean modulus of elasticity parallel to grain in [GPa].
    density : float
        Density of the material in [kg/m3].
    poisson : float
        Poisson's ratio.
    """

    TYPES = {
        "CLT": {
            "fmk": 24.0,
            "fmk_tension": 14.0,
            "E0mean": 12.0,
            "density": 480,
            "poisson": 0.4,
        },
        "LVL_Baubuche": {
            "fmk": 40.0,
            "fmk_tension": 24.0,
            "E0mean": 13.0,
            "density": 690,
            "poisson": 0.4,
        },
        "LVL_Kerto": {
            "fmk": 44.0,
            "fmk_tension": 24.0,
            "E0mean": 13.8,
            "density": 510,
            "poisson": 0.4,
        },
        "Spruce_Rectangular_Beams": {
            "fmk": 22.0,
            "fmk_tension": 11.0,
            "E0mean": 10.0,
            "density": 470,
            "poisson": 0.4,
        },
        "OSB": {
            "fmk": 18.0,
            "fmk_tension": 10.0,
            "E0mean": 4.5,
            "density": 650,
            "poisson": 0.4,
        },
    }

    @property
    def __data__(self):
        # type: () -> dict
        data = super(Timber, self).__data__
        data.update(
            {
                "fmk": self.fmk,
                "fmk_tension": self.fmk_tension,
                "E0mean": self.E0mean,
                "density": self.density,
                "poisson": self.poisson,
            }
        )
        return data

    def __init__(self, fmk, fmk_tension=None, E0mean=10.0, density=500, poisson=0.4, name=None):
        super(Timber, self).__init__(name=name)
        self.fmk = fmk
        self.fmk_tension = fmk_tension or 0.5 * fmk
        self.E0mean = E0mean
        self.density = density
        self.poisson = poisson

    @property
    def rho(self):
        return self.density

    @property
    def nu(self):
        return self.poisson

    @property
    def G(self):
        return self.E0mean / (2 * (1 + self.nu))

    @classmethod
    def from_type(cls, timber_type):
        # type: (str) -> Timber
        """Construct a timber material from a predefined type.

        Parameters
        ----------
        timber_type : {'CLT', 'LVL_Baubuche', 'LVL_Kerto', 'Spruce_Rectangular_Beams'}
            The type of the timber.

        Returns
        -------
        :class:`Timber`

        """
        timber_type = timber_type.replace(" ", "_").capitalize()
        if timber_type not in cls.TYPES:
            raise ValueError("Timber type not supported: {}".format(timber_type))
        params = cls.TYPES[timber_type]
        return cls(**params)
