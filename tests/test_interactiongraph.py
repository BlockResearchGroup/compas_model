from compas_model.model import InteractionGraph


def test_str_print():
    expected_string = "<Graph with 3 nodes, 2 edges>\n0\n- 1: i_1_2\n1\n- 0: i_1_2\n- 2: i_2_3\n2\n- 1: i_2_3\n"

    graph = InteractionGraph()
    n_1 = graph.add_node(element="e_1")
    n_2 = graph.add_node(element="e_2")
    n_3 = graph.add_node(element="e_3")
    graph.add_edge(n_1, n_2, interaction="i_1_2")
    graph.add_edge(n_2, n_3, interaction="i_2_3")
    graph_str = str(graph)

    assert graph_str == expected_string

