# from typing import Generator
from typing import Optional

from compas.datastructures import Graph
from compas_model.elements import Element  # noqa: F401

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
    def __data__(self) -> dict:
        data = super().__data__

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
    def __from_data__(cls, data: dict, guid_element: dict[str, Element]) -> "InteractionGraph":
        graph = super(InteractionGraph, cls).__from_data__(data)
        for node, attr in graph.nodes(data=True):
            element = guid_element[attr["element"]]
            attr["element"] = element  # type: ignore
            element.graphnode = node
        return graph

    def copy(self) -> "InteractionGraph":
        # A custom implementation of copy is needed to allow passing the element dictionary to __from_data__.
        guid_element = {}
        for _, node in self.nodes(data=True):
            element = node["element"]
            guid_element[str(element.guid)] = element
        return self.__from_data__(self.__data__, guid_element)

    def __init__(
        self,
        default_node_attributes: Optional[dict] = None,
        default_edge_attributes: Optional[dict] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            default_node_attributes=default_node_attributes,
            default_edge_attributes=default_edge_attributes,
            name=name,
            **kwargs,
        )

        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(interactions=None)

    def __str__(self) -> str:
        output = super().__str__()

        output += "\n"
        output += self._build_interactions_str()
        return output

    def _build_interactions_str(self) -> str:
        lines = []
        for node in self.nodes():
            lines.append("{}".format(node))
            for nbr in self.neighbors(node):
                edge = node, nbr
                if not self.has_edge(edge):
                    edge = nbr, node

                lines.append(
                    "- {}: {} {} {}".format(
                        nbr,
                        self.edge_attribute(edge, "modifiers"),
                        self.edge_attribute(edge, "contacts"),
                        self.edge_attribute(edge, "collisons"),
                    )  # type: ignore
                )
        return "\n".join(lines) + "\n"

    def clear_edges(self):
        """Clear all the edges and connectivity information of the graph."""
        for u, v in list(self.edges()):
            del self.edge[u][v]
            if v in self.adjacency[u]:
                del self.adjacency[u][v]
            if u in self.adjacency[v]:
                del self.adjacency[v][u]

    def node_element(self, node: int) -> Element:
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
