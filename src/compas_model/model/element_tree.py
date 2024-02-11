from compas.datastructures import Tree
from compas_model.model.element_node import ElementNode
from compas_model.elements import Element


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
        root = ElementNode()
        self.add(root)
        self.model = model

    @property
    def elements(self) -> list[Element]:
        return [node.element for node in self.nodes if isinstance(node, ElementNode)]

    def find_element_node(self, element: Element):
        for node in self.nodes:
            if isinstance(node, ElementNode):
                if node.element is element:
                    return node
        raise ValueError("Element not in tree")
