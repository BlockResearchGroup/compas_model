from .material import Material


class Timber(Material):
    """Class representing a generic timber material.

    Parameters
    ----------
    fck : float
        Characteristic compressive strength in [MPa].
    fctm : float, optional
        Characteristic tensile strength in [MPa].
        If not provided, `fctm = 0.5 * fck` is used.
    Ecm : float, optional
        Mean modulus of elasticity parallel to grain in [GPa].
        If not provided, `Ecm = 10.0` is used.
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
    fck : float
        Characteristic compressive strength in [MPa].
    fctm : float
        Characteristic tensile strength in [MPa].
    Ecm : float
        Mean modulus of elasticity parallel to grain in [GPa].
    density : float
        Density of the material in [kg/m3].
    poisson : float
        Poisson's ratio.
    """

    TYPES = {
        "CLT": {
            "fck": 12.0,
            "fctm": 14.0,
            "Ecm": 12.0,
            "density": 480,
            "poisson": 0.4,
        },
        "LVL_Baubuche": {
            "fck": 20.0,
            "fctm": 24.0,
            "Ecm": 13.0,
            "density": 690,
            "poisson": 0.4,
        },
        "LVL_Kerto": {
            "fck": 22.0,
            "fctm": 24.0,
            "Ecm": 13.8,
            "density": 510,
            "poisson": 0.4,
        },
        "Spruce_Rectangular_Beams": {
            "fck": 11.0,
            "fctm": 11.0,
            "Ecm": 10.0,
            "density": 470,
            "poisson": 0.4,
        },
        "OSB": {
            "fck": 9.0,
            "fctm": 10.0,
            "Ecm": 4.5,
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
                "fck": self.fck,
                "fctm": self.fctm,
                "Ecm": self.Ecm,
                "density": self.density,
                "poisson": self.poisson,
            }
        )
        return data

    def __init__(self, fck, fctm=None, Ecm=10.0, density=500, poisson=0.4, name=None):
        super(Timber, self).__init__(name=name)
        self.fck = fck
        self.fctm = fctm or 0.5 * fck
        self.Ecm = Ecm
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
        return self.Ecm / (2 * (1 + self.nu))

    @classmethod
    def from_type(cls, timber_type):
        # type: (str) -> Timber
        """Construct a timber material from a predefined type.

        Parameters
        ----------
        timber_type : {'CLT', 'LVL_Baubuche', 'LVL_Kerto', 'Spruce_Rectangular_Beams', 'OSB'}
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
