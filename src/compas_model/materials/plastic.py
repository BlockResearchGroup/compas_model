from .material import Material


class Plastic(Material):
    """Class representing a generic plastic material.

    Parameters
    ----------
    fck : float
        Compressive strength in [MPa].
    fctm : float, optional
        Mean tensile strength in [MPa].
        If not provided, `fctm = 0.1 * fck` is used.
    Ecm : float, optional
        Modulus of elasticity in [GPa].
        If not provided, `Ecm = 1.0` is used.
    density : float, optional
        Density of the material in [kg/m3].
        If not provided, 1230 kg/m3 is used.
    poisson : float, optional
        Poisson's ratio.
        If not provided, `poisson = 0.49` is used.
    name : str, optional
        Name of the material.

    Attributes
    ----------
    fck : float
        Compressive strength in [MPa].
    fctm : float
        Mean tensile strength in [MPa].
    Ecm : float
        Modulus of elasticity in [GPa].
    density : float
        Density of the material in [kg/m3].
    poisson : float
        Poisson's ratio.
    """

    TYPES = {
        "Neoprene": {
            "fck": 7.5,
            "fctm": 3.0,
            "Ecm": 1.0,
            "density": 1230,
            "poisson": 0.49,
        },
        "Polyethylene": {
            "fck": 20,
            "fctm": 8.0,
            "Ecm": 1.2,
            "density": 950,
            "poisson": 0.42,
        },
        "Polypropylene": {
            "fck": 35,
            "fctm": 14.0,
            "Ecm": 1.5,
            "density": 900,
            "poisson": 0.42,
        },
    }

    @property
    def __data__(self):
        # type: () -> dict
        data = super(Plastic, self).__data__
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

    def __init__(self, fck, fctm=None, Ecm=1.0, density=1230, poisson=0.49, name=None):
        super(Plastic, self).__init__(name=name)
        self.fck = fck
        self.fctm = fctm or 0.4 * fck  # Adjusted the ratio to be more realistic for plastics
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
    def from_type(cls, plastic_type):
        # type: (str) -> Plastic
        """Construct a plastic material from a predefined type.

        Parameters
        ----------
        plastic_type : {'Neoprene', 'Polyethylene', 'Polypropylene'}
            The type of the plastic.

        Returns
        -------
        :class:`Plastic`

        """
        plastic_type = plastic_type.capitalize()
        if plastic_type not in cls.TYPES:
            raise ValueError("Plastic type not supported: {}".format(plastic_type))
        params = cls.TYPES[plastic_type]
        return cls(**params)
