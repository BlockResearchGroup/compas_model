from pytest import fixture

from compas_model.model import InteractionGraph
from compas_model.interactions import Interaction


@fixture
def mock_graph():
    graph = InteractionGraph()
    n_0 = graph.add_node(element="e_0")
    n_1 = graph.add_node(element="e_1")
    n_2 = graph.add_node(element="e_2")
    i_0_1 = Interaction(name="i_0_1")
    i_1_2 = Interaction(name="i_1_2")
    graph.add_edge(n_0, n_1, interaction=i_0_1)
    graph.add_edge(n_1, n_2, interaction=i_1_2)
    return graph


def test_str_print(mock_graph):
    expected_string = (
        "<Graph with 3 nodes, 2 edges>\n"
        "0\n"
        '- 1: Interaction(name="i_0_1")\n'
        "1\n"
        '- 0: Interaction(name="i_0_1")\n'
        '- 2: Interaction(name="i_1_2")\n'
        "2\n"
        '- 1: Interaction(name="i_1_2")\n'
    )

    assert str(mock_graph) == expected_string


def test_get_interactions(mock_graph):
    interactions = mock_graph.interactions()

    assert len(interactions) == 2
    assert interactions[0].name == "i_0_1"
    assert interactions[1].name == "i_1_2"
