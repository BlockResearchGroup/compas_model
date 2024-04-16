from compas.data import Data


class Material(Data):
    """Base class for representing materials.

    Parameters
    ----------
    density : float
        Density of the material.
    expansion : float, optional
        Thermal expansion coefficient, by default None.

    Attributes
    ----------
    density : float
        Density of the material.
    expansion : float
        Thermal expansion coefficient.
    key : int
        The key index of the material. It is automatically assigned to material
        once it is added to the model.
    """

    def __init__(self, *, density, expansion=None, **kwargs):
        super(Material, self).__init__(**kwargs)
        self.density = density
        self.expansion = expansion
        self._key = None

    @property
    def key(self):
        return self._key

    def __str__(self):
        return """
{}
{}
name        : {}
density     : {}
expansion   : {}
""".format(
            self.__class__.__name__, len(self.__class__.__name__) * "-", self.name, self.density, self.expansion
        )


# ==============================================================================
# linear elastic
# ==============================================================================
class ElasticIsotropic(Material):
    """Elastic, isotropic and homogeneous material

    Parameters
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.

    Attributes
    ----------
    E : float
        Young's modulus E.
    v : float
        Poisson's ratio v.
    G : float
        Shear modulus (automatically computed from E and v)

    """

    def __init__(self, *, E, v, density, expansion=None, name=None, **kwargs):
        super(ElasticIsotropic, self).__init__(density=density, expansion=expansion, name=name, **kwargs)
        self.E = E
        self.v = v

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
            self.name, self.density, self.expansion, self.E, self.v, self.G
        )

    @property
    def G(self):
        return 0.5 * self.E / (1 + self.v)
