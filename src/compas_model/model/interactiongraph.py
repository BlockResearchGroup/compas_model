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
            # this modifies the attributes in place
            # as a consequence, after accessing the __data__ property of the graph,
            # the graph is broken
            # to prevent this, the attribute dict should be copied
            attr = attr.copy()
            attr["element"] = str(attr["element"].guid)
            data["node"][node] = attr
        return data

    @classmethod
    def __from_data__(cls, data, guid_element):
        # type: (dict, dict) -> InteractionGraph
        graph = super(InteractionGraph, cls).__from_data__(data)
        for _, attr in graph.nodes(data=True):
            attr["element"] = guid_element[attr["element"]]  # type: ignore
        return graph

    def copy(self):
        # type: () -> InteractionGraph
        # A custom implementation of copy is needed to allow passing the element dictionary to __from_data__.
        elementdict = {}
        for _, node in self.nodes(data=True):
            element = node["element"]
            elementdict[str(element.guid)] = element
        return self.__from_data__(self.__data__, elementdict)

    def __init__(self, default_node_attributes=None, default_edge_attributes=None, name=None, **kwargs):
        # type: (dict | None, dict | None, str | None, dict) -> None
        super(InteractionGraph, self).__init__(
            default_node_attributes=default_node_attributes,
            default_edge_attributes=default_edge_attributes,
            name=name,
            **kwargs,
        )
        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(interactions=None)

    def __str__(self):
        # type: () -> str
        output = super(InteractionGraph, self).__str__()
        output += "\n"
        output += self._build_interactions_str()
        return output

    def _build_interactions_str(self):
        # type: () -> str
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
                        self.edge_interactions(edge),  # type: ignore
                    )  # type: ignore
                )
        return "\n".join(lines) + "\n"

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

    def edge_interactions(self, edge):
        # type: (tuple[int, int]) -> list[Interaction]
        """Get the element associated with the node.

        Parameters
        ----------
        edge : tuple[int, int]
            The identifier of the edge.

        Returns
        -------
        :class:`compas_model.interactions.Interaction`

        """
        return self.edge_attribute(edge, "interactions")  # type: ignore

    def interactions(self):
        # type: () -> list[Interaction]
        """Get the interactions in the graph.

        Returns
        -------
        list[:class:`compas_model.interactions.Interaction`]

        """
        return [interaction for edge in self.edges() for interaction in self.edge_interactions(edge)]
