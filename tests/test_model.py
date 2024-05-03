from pytest import fixture

from compas.data import json_dumps
from compas.data import json_loads

from compas_model.model import Model
from compas_model.elements import Element
from compas_model.interactions import Interaction


@fixture
def mock_model():
    model = Model()
    a = Element(name="a")
    b = Element(name="b")
    c = Element(name="c")
    group = model.add_group(name="group_ab")
    model.add_element(a, parent=group)
    model.add_element(b, parent=group)
    model.add_element(c)
    model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))
    model.add_interaction(b, c, interaction=Interaction(name="i_b_c"))
    return model


def test_serialize_model(mock_model):
    guids = [str(e.guid) for e in mock_model.elementlist]
    a = mock_model[0]
    b = mock_model[1]
    c = mock_model[2]

    mock_model: Model = json_loads(json_dumps(mock_model))

    assert len(mock_model.elementlist) == 3
    assert guids == [str(e.guid) for e in mock_model.elementlist]
    assert mock_model.has_interaction(a, c)
    assert mock_model.has_interaction(b, c)

