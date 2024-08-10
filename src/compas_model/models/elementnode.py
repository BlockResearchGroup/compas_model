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
        # type: () -> dict
        data = super(ElementNode, self).__data__
        data["element"] = None if not self.element else str(self.element.guid)
        return data

    @classmethod
    def __from_data__(cls, data):
        # type: (dict) -> ElementNode
        raise Exception("Serialisation outside model context not allowed.")

    def __init__(self, element=None, **kwargs):
        # type: (Element | None, str | None) -> None
        super(ElementNode, self).__init__(**kwargs)
        if element:
            element.tree_node = self
        self.element = element

    def __getitem__(self, index):
        # type: (int) -> ElementNode
        return self.children[index]
