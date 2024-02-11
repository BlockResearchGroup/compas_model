from compas.datastructures import Graph


class InteractionGraph(Graph):
    """Class representing the interactions between elements in a model.

    Notes
    -----
    Ideally, graph (and mesh) are rewritten to use dedicated classes for nodes and edges.
    This will allow more fine-grained control over the (types of) attributes added to nodes and edges.
    It will also provide a much more intuitive API.

    """

    @property
    def __data__(self):
        data = super().__data__
        for node, attr in data["node"].items():
            attr["element"] = str(attr["element"].guid)
        return data

    @classmethod
    def __from_data__(cls, data, guid_element):
        graph = super().__from_data__(data)
        for _, attr in graph.nodes(data=True):
            attr["element"] = guid_element[attr["element"]]
        return graph

    def __init__(
        self,
        default_node_attributes=None,
        default_edge_attributes=None,
        name=None,
        **kwargs
    ):
        super().__init__(
            default_node_attributes=default_node_attributes,
            default_edge_attributes=default_edge_attributes,
            name=name,
            **kwargs,
        )
        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(interaction=None)
