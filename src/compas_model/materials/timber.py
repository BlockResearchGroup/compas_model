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
