# from compas_model.models import Model
# from compas_model.elements import PlateElement
# from compas_model.interactions import Interaction
# from compas.datastructures import Mesh
# from typing import Optional

# from compas.geometry import Frame
# from compas.geometry import Box
# from compas.geometry import Transformation


# class MyElement(PlateElement):
#     """Class representing an element for testing."""

#     def __init__(
#         self,
#         size: float = 0.1,
#         frame: Frame = Frame.worldXY(),
#         transformation: Optional[Transformation] = None,
#         name: Optional[str] = None,
#     ) -> "MyElement":
#         super().__init__(frame=frame, transformation=transformation, name=name)

#         self.size: float = size

#     def compute_elementgeometry(self) -> Mesh:
#         """Element geometry in the local frame.

#         Returns
#         -------
#         :class:`compas.datastructures.Mesh`

#         """

#         return Box(self.size, self.size, self.size, self.frame).to_mesh()


# def test_is_dirty_setter():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c
#     model.add_interaction(a, b, interaction=Interaction(name="i_b_c"))  # a affects b
#     a.is_dirty = False
#     b.is_dirty = False
#     c.is_dirty = False
#     d.is_dirty = False

#     elements = list(model.elements())

#     assert not elements[0].is_dirty
#     assert not elements[1].is_dirty
#     assert not elements[2].is_dirty
#     assert not elements[3].is_dirty

#     elements[0].is_dirty = True

#     assert elements[0].is_dirty
#     assert elements[1].is_dirty
#     assert elements[2].is_dirty
#     assert not elements[3].is_dirty


# def test_is_dirty_add_interaction():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)

#     model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # c affects a
#     for element in model.elements():
#         element.modelgeometry  # All elements is_dirty is set to False
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # c affects b

#     elements = list(model.elements())
#     assert not elements[0].is_dirty
#     assert not elements[1].is_dirty
#     assert elements[2].is_dirty
#     assert not elements[3].is_dirty


# def test_is_dirty_remove_interaction():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)
#     model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

#     for element in model.elements():
#         element.is_dirty = False
#     model.remove_interaction(a, b)  # a affects b
#     model.remove_interaction(a, c)  # a affects c

#     elements = list(model.elements())
#     assert not elements[0].is_dirty
#     assert elements[1].is_dirty
#     assert elements[2].is_dirty
#     assert not elements[3].is_dirty


# def test_is_dirty_remove_element_0():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)
#     model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

#     for element in model.elements():
#         element.modelgeometry  # All element is_dirty is set to False

#     model.remove_element(a)  # b and c is_dirty is set to True

#     elements = list(model.elements())
#     assert elements[0].is_dirty
#     assert elements[1].is_dirty
#     assert not elements[2].is_dirty


# def test_is_dirty_remove_element_1():
#     model = Model()
#     a = MyElement(name="a")
#     b = MyElement(name="b")
#     c = MyElement(name="c")
#     d = MyElement(name="d")
#     model.add_element(a)
#     model.add_element(b)
#     model.add_element(c)
#     model.add_element(d)
#     model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

#     for element in model.elements():
#         element.modelgeometry  # All element is_dirty is set to False

#     model.remove_element(b)  # b and c is_dirty is set to True

#     elements = list(model.elements())
#     assert not elements[0].is_dirty
#     assert not elements[1].is_dirty
#     assert not elements[2].is_dirty

from compas_model.elements import Element  # noqa: F401


def test_import():
    assert True
