from .material import Material


class Steel(Material):

    strength_classes = {
        "S235": {"fy": 235, "fu": 360},
        "S275": {"fy": 275, "fu": 430},
        "S355": {"fy": 355, "fu": 490},
        "S450": {"fy": 450, "fu": 550},
    }

    @property
    def __data__(self):
        # type: () -> dict
        data = super(Steel, self).__data__
        data.update(
            {
                "fy": self.fy,
                "fu": self.fu,
            }
        )
        return data

    def __init__(self, fy, fu, name=None):
        super(Steel, self).__init__(name=name)
        self.fy = fy
        self.fu = fu
        self.E = 210
        self.poisson = 0.3
        self.density = 7850

    @property
    def rho(self):
        return self.density

    @property
    def nu(self):
        return self.poisson

    @property
    def G(self):
        return self.E / (2 * (1 + self.nu))

    @classmethod
    def from_strength_class(cls, strength_class):
        # type: (str) -> Steel
        """Construct a steel material from a steel strength class.

        Parameters
        ----------
        strength_class : {'S235', 'S275', 'S355', 'S450'}
            The strength class.

        Returns
        -------
        :class:`Steel`

        """
        strength_class = strength_class.upper()
        if strength_class not in cls.strength_classes:
            raise ValueError("This strength class is not supported: {}".format(strength_class))
        params = cls.strength_classes[strength_class]
        return cls(**params)
