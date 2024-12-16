from pytest import fixture

from compas_model.models import Model
from compas_model.elements import BlockElement
from compas_model.interactions import Interaction
from compas.datastructures import Mesh


@fixture
def my_model():
    model = Model()
    a = BlockElement(name="a", shape=Mesh.from_polyhedron(6))
    b = BlockElement(name="b", shape=Mesh.from_polyhedron(6))
    c = BlockElement(name="c", shape=Mesh.from_polyhedron(6))
    d = BlockElement(name="d", shape=Mesh.from_polyhedron(6))
    model.add_element(a)
    model.add_element(b)
    model.add_element(c)
    model.add_element(d)
    a.is_dirty = False
    b.is_dirty = False
    c.is_dirty = False
    d.is_dirty = False
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))
    model.add_interaction(a, b, interaction=Interaction(name="i_b_c"))
    return model


def test_is_dirty(my_model):
    elements = list(my_model.elements())
    assert not elements[0].is_dirty
    assert not elements[1].is_dirty
    assert not elements[2].is_dirty
    assert not elements[3].is_dirty

    elements[0].is_dirty = True

    assert elements[0].is_dirty
    assert elements[1].is_dirty
    assert elements[2].is_dirty
    assert not elements[3].is_dirty
