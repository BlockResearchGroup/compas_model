from compas.datastructures import Tree
from compas_model.model.element_node import ElementNode
from compas_model.model.group_node import GroupNode
from compas_model.elements import Element
from typing import Union


class ElementTree(Tree):
    @property
    def __data__(self):
        data = super().__data__
        return data

    @classmethod
    def __from_data__(cls, data):
        raise Exception(
            "ElementTree objects should only be serialised through a Model object."
        )

    def __init__(self, name: str = None, model=None):
        super().__init__(name=name)
        root = GroupNode("root")
        self.add(root)
        self.model = model

    def __getitem__(self, value:Union[int,str]):
        return self.root[value]

    @property
    def elements(self) -> list[Element]:
        return [node.element for node in self.nodes if isinstance(node, ElementNode)]

    def find_element_node(self, element: Element):
        for node in self.nodes:
            if isinstance(node, ElementNode):
                if node.element is element:
                    return node
        raise ValueError("Element not in tree")

    def find_group_node(self, groupnode: GroupNode):
        for node in self.nodes:
            if isinstance(node, GroupNode):
                if node is groupnode:
                    return node
        raise ValueError("Group not in tree")


