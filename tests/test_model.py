# from pytest import fixture

# from compas.data import json_dumps
# from compas.data import json_loads

# from compas_model.models import Model
# from compas_model.elements import PlateElement
# from compas_model.interactions import Interaction


# @fixture
# def mock_model() -> Model:
#     model = Model()
#     a = PlateElement(name="a")
#     b = PlateElement(name="b")
#     c = PlateElement(name="c")
#     model.add_element(a)
#     model.add_element(b, parent=a)
#     model.add_element(c)
#     model.add_interaction(a, c, interaction=Interaction(name="i_a_c"))
#     model.add_interaction(b, c, interaction=Interaction(name="i_b_c"))
#     return model


# def test_serialize_model(mock_model: Model):
#     guids = [str(e.guid) for e in mock_model.elements()]
#     elements = list(mock_model.elements())
#     a = elements[0]
#     b = elements[1]
#     c = elements[2]

#     mock_model: Model = json_loads(json_dumps(mock_model))

#     assert len(list(mock_model.elements())) == 3
#     assert guids == [str(e.guid) for e in mock_model.elements()]
#     assert mock_model.has_interaction(a, c)
#     assert mock_model.has_interaction(b, c)


# def test_model_deepcopy(mock_model: Model):
#     c_model = mock_model.copy()

#     assert c_model is not None
#     assert c_model.graph is not None
#     assert c_model.tree is not None
#     assert len(c_model.tree.elements) == 3

from compas_model.models import Model  # noqa: F401


def test_import():
    assert True
