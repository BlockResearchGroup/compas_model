from compas.datastructures import TreeNode
from compas_model.elements import Element


class ElementNode(TreeNode):
    """Class representing nodes containing elements in an element tree.

    Parameters
    ----------
    element : :class:`Element`
        The element contained in the node.

    Attributes
    ----------
    element : :class:`Element`
        The element contained in the node.

    Notes
    -----
    This object will raise an Exception,
    when it is (de)serialised independently, outside the context of a Model.

    """

    @property
    def __data__(self):
        return {
            "element": None if not self.element else str(self.element.guid),
            "children": [child.__data__ for child in self.children],
        }

    @classmethod
    def __from_data__(cls, data):
        raise ValueError(
            "ElementNode objects should only be serialised through a Model object."
        )

    def __init__(self, element: Element = None):
        super().__init__()
        self.element = element
        if self.element:
            element.tree_node = self

    def add_element(self, element: Element):
        """Add element to ElementNode.

        Triple Behavior:

        1. Create ElementNode from element.
        2. Add this node to parent children list.
        3. Add an element to the base dictionary of the Model class.
        4. Add an element to the graph.


        Parameters
        ----------
        element : :class:`compas_model.elements.Element`
            Element object or any class that inherits from Element class.

        Returns
        -------
        :class:`compas_model.model.ElementNode`
            ElementNode object or any class that inherits from ElementNode class.

        """

        return self.tree.model.add_element(element, self.element)
