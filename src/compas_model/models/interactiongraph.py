from typing import TYPE_CHECKING

from compas.datastructures import Graph
from compas_model.elements import Element  # noqa: F401

if TYPE_CHECKING:
    from compas_model.models import Model


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

    model: "Model"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.update_default_node_attributes(element=None)
        self.update_default_edge_attributes(modifiers=None, contacts=None)
        self.model = None  # type: ignore

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
                    "- {}: {} {}".format(
                        nbr,
                        self.edge_attribute(edge, "modifiers"),
                        self.edge_attribute(edge, "contacts"),
                    )  # type: ignore
                )
        return "\n".join(lines) + "\n"

    def add_element(self, element: Element) -> int:
        node = self.add_node(element=str(element.guid))
        element.graphnode = node
        return node

    def node_element(self, node: int) -> Element:
        """Get the element associated with the node.

        Parameters
        ----------
        node : int
            The identifier of the node.

        Returns
        -------
        Element

        """
        guid: str = self.node_attribute(node, "element")  # type: ignore
        return self.model._elements[guid]

    def clear_edges(self):
        """Clear all the edges and connectivity information of the graph."""
        for u, v in list(self.edges()):
            del self.edge[u][v]
            if v in self.adjacency[u]:
                del self.adjacency[u][v]
            if u in self.adjacency[v]:
                del self.adjacency[v][u]
