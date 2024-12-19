from pytest import fixture

from compas_model.models import Model
from compas_model.elements import BlockElement
from compas_model.interactions import Interaction
from compas.datastructures import Mesh
from compas_model.elements import BeamIProfileElement
from compas_model.elements import BeamSquareElement
from compas_model.elements import ColumnHeadCrossElement
from compas_model.elements import ColumnRoundElement
from compas_model.elements import ColumnSquareElement
from compas_model.elements import PlateElement
from compas_model.elements import ScrewElement


def test_element_serialization():
    elements = [
        BeamIProfileElement(),
        BeamSquareElement(),
        ColumnHeadCrossElement(),
        ColumnRoundElement(),
        ColumnSquareElement(),
        PlateElement(),
        ScrewElement(),
    ]

    for element in elements:
        copied_element = element.copy()
        assert copied_element is not element, f"Copied element should be a new instance for {type(element).__name__}"
        assert copied_element.__data__ == element.__data__, f"Copied element data should match original for {type(element).__name__}"
        print(f"{element.name} copied successfully")


def test_is_dirty_setter():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c
    model.add_interaction(a, b, interaction=Interaction(name="i_b_c"))  # a affects b
    a.is_dirty = False
    b.is_dirty = False
    c.is_dirty = False
    d.is_dirty = False

    elements = list(model.elements())

    assert not elements[0].is_dirty
    assert not elements[1].is_dirty
    assert not elements[2].is_dirty
    assert not elements[3].is_dirty

    elements[0].is_dirty = True

    assert elements[0].is_dirty
    assert elements[1].is_dirty
    assert elements[2].is_dirty
    assert not elements[3].is_dirty


def test_is_dirty_add_interaction():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)

    model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # c affects a
    for element in model.elements():
        element.modelgeometry  # All element is_dirty is set to False
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # c affects b

    elements = list(model.elements())
    assert not elements[0].is_dirty
    assert not elements[1].is_dirty
    assert elements[2].is_dirty
    assert not elements[3].is_dirty


def test_is_dirty_remove_interaction():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)
    model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

    for element in model.elements():
        element.is_dirty = False
    model.remove_interaction(a, b)  # a affects b
    model.remove_interaction(a, c)  # a affects c

    elements = list(model.elements())
    assert not elements[0].is_dirty
    assert elements[1].is_dirty
    assert elements[2].is_dirty
    assert not elements[3].is_dirty


def test_is_dirty_remove_element_0():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)
    model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

    for element in model.elements():
        element.modelgeometry  # All element is_dirty is set to False

    model.remove_element(a)  # b and c is_dirty is set to True

    elements = list(model.elements())
    assert elements[0].is_dirty
    assert elements[1].is_dirty
    assert not elements[2].is_dirty


def test_is_dirty_remove_element_1():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)
    model.add_interaction(a, b, interaction=Interaction(name="i_a_b"))  # a affects b
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))  # a affects c

    for element in model.elements():
        element.modelgeometry  # All element is_dirty is set to False

    model.remove_element(b)  # b and c is_dirty is set to True

    elements = list(model.elements())
    assert not elements[0].is_dirty
    assert not elements[1].is_dirty
    assert not elements[2].is_dirty
