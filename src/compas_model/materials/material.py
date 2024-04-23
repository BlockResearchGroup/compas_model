from compas.data import Data


class Material(Data):
    """Base class for representing materials.

    Parameters
    ----------
    name : str
        Name of the material.
    rho : float
        Density of the material.
    eps : float, optional
        Thermal expansion coefficient, by default None.

    Attributes
    ----------
    name : str
        Name of the material.
    rho : float
        Density of the material.
    eps : float
        Thermal expansion coefficient.
    """

    def __init__(self, *, name, rho, eps=None, **kwargs):
        super(Material, self).__init__(**kwargs)
        self.name = name
        self.rho = rho
        self.eps = eps

    def __eq__(self, value):
        return self.rho == value.rho and self.eps == value.eps

    def __str__(self):
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}
""".format(
            self.__class__.__name__, len(self.__class__.__name__) * "-", self.name, self.rho, self.eps
        )


# ==============================================================================
# linear elastic
# ==============================================================================


class ElasticIsotropic(Material):
    """Elastic, isotropic and homogeneous material.

    Parameters
    ----------
    name : str
        Name of the material.
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    rho : float
        Density of the material.
    eps : float, optional
        Thermal expansion coefficient, by default None.

    Attributes
    ----------
    name : str
        Name of the material.
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float, read-only
        Shear modulus (automatically computed from E and v).

    """

    def __init__(self, *, name, E, v, rho, eps=None, **kwargs):
        super(ElasticIsotropic, self).__init__(name=name, rho=rho, eps=eps, **kwargs)
        self.name = name
        self.E = E
        self.v = v

    def __eq__(self, value):
        return self.E == value.E and self.v == value.v and self.rho == value.rho and self.eps == value.eps

    def __str__(self):
        return """
ElasticIsotropic Material
-------------------------
name        : {}
density     : {}
expansion   : {}

E : {}
v : {}
G : {}
""".format(
            self.name, self.rho, self.eps, self.E, self.v, self.G
        )

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)
