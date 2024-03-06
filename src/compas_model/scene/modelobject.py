from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas.geometry  # noqa: F401
from compas.scene import SceneObject

import compas_model.model  # noqa: F401


class ModelObject(SceneObject):
    def __init__(
        self,
        model,
        show_tree=False,  # type: bool
        show_graph=False,  # type: bool
        show_elements=True,  # type: bool
        show_interactions=True,  # type: bool
        show_element_faces=True,  # type: bool
        **kwargs,  # type: dict
    ):  # type: (...) -> None
        super(ModelObject, self).__init__(item=model, **kwargs)

        self._model = model

        self.show_tree = show_tree
        self.show_graph = show_graph
        self.show_elements = show_elements
        self.show_interactions = show_interactions

        elementkwargs = kwargs.copy()
        if "show_faces" in elementkwargs:
            del elementkwargs["show_faces"]

        for element in model.elementlist:
            self.add(element, show_faces=show_element_faces, **elementkwargs)

        # for edge in model.graph.edges():
        #     interaction = model.graph.edge_attribute(edge, name="interaction")
        #     self.add(interaction, show_faces=show_interaction_faces,  **kwargs)

    @property
    def model(self):
        # type: () -> compas_model.model.Model
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self._transformation = None

    @property
    def transformation(self):
        # type: () -> compas.geometry.Transformation | None
        return self._transformation

    @transformation.setter
    def transformation(self, transformation):
        self._transformation = transformation

    def draw(self):
        """draw the model.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def clear(self):
        """Clear all components of the model.

        Returns
        -------
        None

        """
        raise NotImplementedError
