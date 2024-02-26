from compas.datastructures import Graph
from compas_model.elements import Element  # noqa: F401
from compas_model.interactions import Interaction  # noqa: F401


# Ideally, graph (and mesh) are rewritten to use dedicated classes for nodes and edges.
# This will allow more fine-grained control over the (types of) attributes added to nodes and edges.
# It will also provide a much more intuitive API.


class InteractionGraph(Graph):
    """Class representing the interactions between elements in a model.

    Parameters
    ----------
    default_node_attributes : dict, optional
        The default attributes for nodes.
    default_edge_attributes : dict, optional
        The default attributes for edges.

    Notes
    -----
    The main purpose of this class customisation is to modify the data serialisation behaviour
    of the graph in the context of element interaction modelling in a model.

    """

    @property
    def __data__(self):
        # type: () -> dict
        data = super(InteractionGraph, self).__data__
        for node, attr in data["node"].items():
            attr["element"] = str(attr["element"].guid)
        return data

    @classmethod
    def __from_data__(cls, data, guid_element):
        # type: (dict, dict) -> InteractionGraph
        graph = super(InteractionGraph, cls).__from_data__(data)
        for node, attr in graph.nodes(data=True):
            attr["element"] = guid_element[attr["element"]]  # type: ignore
        return graph

    def __init__(
        self,
        default_node_attributes=None,
        default_edge_attributes=None,
        name=None,
        **kwargs
    ):
        # type: (dict | None, dict | None, str | None, dict) -> None
        super().__init__(
            default_node_attributes=default_node_attributes,
            default_edge_attributes=default_edge_attributes,
            name=name,
            **kwargs,
        )
        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(interaction=None)

    def node_element(self, node):
        # type: (int) -> Element
        """Get the element associated with the node.

        Parameters
        ----------
        node : int
            The identifier of the node.

        Returns
        -------
        :class:`compas_model.elements.Element`

        """
        return self.node_attribute(node, "element")  # type: ignore

    def edge_interaction(self, edge):
        # type: (tuple[int, int]) -> Interaction
        """Get the element associated with the node.

        Parameters
        ----------
        edge : tuple[int, int]
            The identifier of the edge.

        Returns
        -------
        :class:`compas_model.interactions.Interaction

        """
        return self.edge_attribute(edge, "interaction")  # type: ignore

    def print_interactions(self):
        """Print the interactions contained in the graph."""
        lines = []
        for node in self.nodes():
            lines.append("{}".format(node))
            for nbr in self.neighbors(node):
                edge = node, nbr
                if not self.has_edge(edge):
                    edge = nbr, node
                lines.append(
                    "- {}: {}".format(
                        nbr,
                        self.edge_interaction(edge),  # type: ignore
                    )  # type: ignore
                )
        print("\n".join(lines))
