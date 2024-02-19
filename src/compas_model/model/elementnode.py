from compas.datastructures import TreeNode
from compas_model.elements import Element  # noqa: F401


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

    def __init__(self, element):
        # type: (Element) -> None
        super(ElementNode, self).__init__()
        element.tree_node = self
        self.element = element
