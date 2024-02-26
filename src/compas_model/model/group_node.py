from compas.datastructures import TreeNode
from compas_model.elements import Element
from typing import Union,List


class GroupNode(TreeNode):
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
            "GroupNode objects should only be serialised through a Model object."
        )

    def __init__(self, name):
        super().__init__(name=name)

    def __getitem__(self, value:Union[int,str]):
        if value is int:
            return self.children[value]
        else:
            for node in self.children:
                if node.name == value:
                    return node

    def __iter__(self):
        return iter(self.children)

    def add_element(self, element: Element):
        """Add element to GroupNode.

        Triple Behavior:

        1. Create GroupNode from element.
        2. Add this node to parent children list.
        3. Add an element to the base dictionary of the Model class.
        4. Add an element to the graph.


        Parameters
        ----------
        element : :class:`compas_model.elements.Element`
            Element object or any class that inherits from Element class.

        Returns
        -------
        :class:`compas_model.model.GroupNode`
            GroupNode object or any class that inherits from GroupNode class.

        """

        return self.tree.model.add_element(element, self)

    def add_elements(self, elements: List[Element]):
        for i in elements:
            self.add_element(i)



    def add_group(self, name: str):
        # Create a new ElementNode and assign the parent:
        group_node = GroupNode(name=name)
        self.add(group_node)
        return group_node
