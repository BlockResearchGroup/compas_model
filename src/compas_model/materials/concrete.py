from typing import Literal
from typing import Optional

from .material import Material


class Concrete(Material):
    """Class representing a generic concrete material.

    Parameters
    ----------
    fck : float
        Characteristic cylinder compressive strength in [MPa].
    fck_cube : float, optional
        Characteristic cube compressive strength in [MPa].
        If not provided, `fck_cube = 1.25 * fck` is used.
    fctm : float, optional
        Mean tensile strength in [MPa].
        If not provided, `fctm = 0.1 * fck` is used.
    Ecm : float, optional
        Modulus of elasticity in [GPa].
    density : float, optional
        Density of the material in [kg/m3].
        If not provided, 2400 kg/m3 is used.
    poisson : float, optional
        Poisson's ratio.
        If not provided, `poisson = 0.2` is used.
    name : str, optional
        Name of the material.

    Attributes
    ----------
    fck : float
        Characteristic cylinder compressive strength in [MPa].
    fck_cube : float
        Characteristic cube compressive strength in [MPa].
    fcm : float
        Mean compressive strength as `fcm = fck + 8 Mpa`.
    fctm : float
        Mean tensile strength in [MPa].
    Ecm : float
        Modulus of elasticity in [MPa].

    """

    STRENGTH_CLASSES = {
        "C10": {
            "fck": 10,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
        "C15": {
            "fck": 15,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
        "C20": {
            "fck": 20,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
        "C25": {
            "fck": 25,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
        "C30": {
            "fck": 30,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
        "C35": {
            "fck": 35,
            "fck_cube": None,
            "fcm": None,
            "fctm": None,
            "Ecm": None,
        },
    }

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update(
            {
                "fck": self.fck,
                "fck_cube": self.fck_cube,
                "fcm": self.fcm,
                "fctm": self.fctm,
                "Ecm": self.Ecm,
                "density": self.density,
                "poisson": self.poisson,
            }
        )
        return data

    def __init__(
        self,
        fck: float,
        fck_cube: Optional[float] = None,
        fcm: Optional[float] = None,
        fctm: Optional[float] = None,
        Ecm: Optional[float] = None,
        density: float = 2400,
        poisson: float = 0.2,
        name: Optional[str] = None,
    ):
        super().__init__(name=name)

        self.fck = fck
        self.fck_cube = fck_cube or 1.25 * fck
        self.fcm = fcm
        self.fctm = fctm or 0.1 * fck
        self.Ecm = Ecm
        self.density = density
        self.poisson = poisson

    @property
    def rho(self) -> float:
        return self.density

    @property
    def nu(self) -> float:
        return self.poisson

    @property
    def G(self) -> float:
        return self.Ecm / (2 * (1 + self.nu))

    @classmethod
    def from_strength_class(cls, strength_class: Literal["C10", "C15", "C20", "C25", "C30", "C35"]) -> "Concrete":
        """Construct a concrete material from a strength class.

        Parameters
        ----------
        strength_class : {'C10', 'C15', 'C20', 'C25', 'C30', 'C35'}
            The strength class of the concrete.

        Returns
        -------
        :class:`Concrete`

        """
        strength_class = strength_class.upper()
        if strength_class not in cls.STRENGTH_CLASSES:
            raise ValueError("Strength class not supported: {}".format(strength_class))
        params = cls.STRENGTH_CLASSES[strength_class]
        return cls(**params)
