from typing import Any
from typing import cast

from compas.scene import SceneObject
from compas_model.models import Model


class ModelObject(SceneObject):
    """Represent a model as a stable container in a scene.

    Construct the hierarchy explicitly by adding element objects to the scene
    with this object as their parent.

    """

    def __init__(self, **kwargs: Any) -> None:
        # ViewerScene supplies primitive colors to registered data types. A
        # model container has no primitives of its own.
        for key in ("pointcolor", "linecolor", "surfacecolor"):
            kwargs.pop(key, None)
        super().__init__(**kwargs)

    @property
    def model(self) -> Model:
        """Model: The represented model."""
        return cast(Model, self.item)
