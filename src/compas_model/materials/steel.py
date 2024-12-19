from typing import Literal
from typing import Optional

from .material import Material


class Steel(Material):
    STRENGTH_CLASSES: dict[str, dict[str, float]] = {
        "S235": {"fy": 235, "fu": 360},
        "S275": {"fy": 275, "fu": 430},
        "S355": {"fy": 355, "fu": 490},
        "S450": {"fy": 450, "fu": 550},
    }

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update(
            {
                "fy": self.fy,
                "fu": self.fu,
            }
        )
        return data

    def __init__(self, fy: float, fu: float, name: Optional[str] = None) -> None:
        super().__init__(name=name)

        self.fy = fy
        self.fu = fu
        self.E = 210
        self.poisson = 0.3
        self.density = 7850

    @property
    def rho(self) -> float:
        return self.density

    @property
    def nu(self) -> float:
        return self.poisson

    @property
    def G(self) -> float:
        return self.E / (2 * (1 + self.nu))

    @classmethod
    def from_strength_class(cls, strength_class: Literal["S235", "S275", "S355", "S450"]) -> "Steel":
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
        if strength_class not in cls.STRENGTH_CLASSES:
            raise ValueError("This strength class is not supported: {}".format(strength_class))
        params = cls.STRENGTH_CLASSES[strength_class]
        return cls(**params)
