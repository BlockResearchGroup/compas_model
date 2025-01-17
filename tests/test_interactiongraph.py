# from pytest import fixture

# from compas_model.models import InteractionGraph
# from compas_model.elements import PlateElement
# from compas_model.interactions import Interaction


# @fixture
# def mock_graph():
#     graph = InteractionGraph()
#     n_0 = graph.add_node(element=PlateElement(name="e_0"))
#     n_1 = graph.add_node(element=PlateElement(name="e_1"))
#     n_2 = graph.add_node(element=PlateElement(name="e_2"))
#     i_0_1 = Interaction(name="i_0_1")
#     i_1_2 = Interaction(name="i_1_2")
#     graph.add_edge(n_0, n_1, interactions=[i_0_1])
#     graph.add_edge(n_1, n_2, interactions=[i_1_2])
#     return graph


# def test_str_print(mock_graph):
#     expected_string = (
#         "<Graph with 3 nodes, 2 edges>\n"
#         "0\n"
#         '- 1: [Interaction(name="i_0_1")]\n'
#         "1\n"
#         '- 0: [Interaction(name="i_0_1")]\n'
#         '- 2: [Interaction(name="i_1_2")]\n'
#         "2\n"
#         '- 1: [Interaction(name="i_1_2")]\n'
#     )

#     assert str(mock_graph) == expected_string


# def test_get_interactions(mock_graph):
#     interactions = list(mock_graph.interactions())

#     assert len(interactions) == 2
#     assert interactions[0].name == "i_0_1"
#     assert interactions[1].name == "i_1_2"


# def test_interaction_deepcopy(mock_graph):
#     c_graph = mock_graph.copy()

#     assert c_graph.number_of_nodes() == 3
