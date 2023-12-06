from compas.geometry import Point
from compas_model.elements.element import Element
from compas_model.model.group_node import ElementNode
from compas_model.model.group_node import GroupNode
from compas_model.model import Model
from compas.data import json_dump, json_load


def create_model():

    # create model
    model = Model()

    # add group nodes - a typical tree node with a name and geometry
    car = model.add_group(name="car", geometry=None)  # type: ignore
    interior = model.add_group(name="interior", geometry=None)  # type: ignore
    seats = interior.add_group(name="seats", geometry=None)  # type: ignore
    front_seat = seats.add_group(name="front_seat", geometry=None)  # type: ignore
    wheel = car.add_group(name="wheel", geometry=Point(0, 0, 0))  # type: ignore

    # add element nodes - a "special" tree node with a name and element
    wheel.add_element(name="spoke1", element=Element.from_frame(1, 10, 1))  # type: ignore
    wheel.add_element(name="spoke2", element=Element.from_frame(5, 10, 1))  # type: ignore
    front_seat.add_element(name="seat1", element=Element.from_frame(1, 10, 1))  # type: ignore
    front_seat.add_element(name="seat2", element=Element.from_frame(5, 10, 1))  # type: ignore

    # print the model to preview the tree structure
    # model.print()

    # output
    return model


def create_model_with_interactions():

    # create model
    model = Model()

    # add group nodes - a typical tree node with a name and geometry
    car = model.add_group(name="car", geometry=None)  # type: ignore
    wheel = car.add_group(name="wheel", geometry=Point(0, 0, 0))  # type: ignore

    # add element nodes - a "special" tree node with a name and element
    spoke1 = wheel.add_element(name="spoke1", element=Element.from_frame(1, 10, 1))  # type: ignore
    spoke2 = wheel.add_element(name="spoke2", element=Element.from_frame(5, 10, 1))  # type: ignore
    spoke3 = wheel.add_element(name="spoke3", element=Element.from_frame(10, 10, 1))  # type: ignore

    # add interactions
    model.add_interaction(spoke1, spoke2)
    model.add_interaction(spoke1, spoke3)
    model.add_interaction(spoke2, spoke3)

    # print the model to preview the tree structure
    model.print()

    # output
    return model


def create_model_without_hierarchy():

    # create model
    model = Model()

    # add element nodes - a "special" tree node with a name and element
    spoke1 = model.add_element(name="spoke1", element=Element.from_frame(1, 10, 1))  # type: ignore
    spoke2 = model.add_element(name="spoke2", element=Element.from_frame(5, 10, 1))  # type: ignore
    spoke3 = model.add_element(name="spoke3", element=Element.from_frame(10, 10, 1))  # type: ignore

    # add interactions
    model.add_interaction(spoke1, spoke2)
    model.add_interaction(spoke1, spoke3)
    model.add_interaction(spoke2, spoke3)

    # print the model to preview the tree structure
    model.print()

    # output
    return model


def copy_model():
    # ==========================================================================
    # create elements and a Node and a ElementTree and a Model
    # ==========================================================================
    e0 = Element(name="beam", geometry_simplified=Point(0, 0, 0))
    e1 = Element(name="beam", geometry_simplified=Point(0, 5, 0))
    e2 = Element(name="block", geometry_simplified=Point(0, 0, 0))
    e3 = Element(name="block", geometry_simplified=Point(0, 5, 0))

    model = (
        Model()
    )  # the root of hierarchy automatically initializes the root node as <my_model>
    truss1 = model.add_group("truss1")
    truss2 = model.add_group("truss2")
    truss1.add_element(e0.name, e0)
    truss1.add_element(e1.name, e1)
    truss2.add_element(e2.name, e2)
    truss2.add_element(e3.name, e3)
    model.print()

    model.add_interaction(e0, e1)

    print("BEFORE COPY")
    model.print()
    model.print_interactions()
    # ==========================================================================
    # copy the model
    # ==========================================================================
    print("AFTER COPY")
    model_copy = model.copy()
    model_copy.print()
    model_copy.print_interactions()


def serialize_element():
    # ==========================================================================
    # create elements and a Node
    # ==========================================================================
    e = Element(name="beam", geometry_simplified=Point(0, 0, 0))
    # ==========================================================================
    # serialize the model_node
    # =========================================================================
    print(e)
    json_dump(e, "data/model_how_to_use_it_element.json", pretty=True)
    json_load("data/model_how_to_use_it_element.json")
    print(e)


def serialize_model_node():
    # ==========================================================================
    # create elements and a Node
    # ==========================================================================
    group_node = GroupNode(name="timber1", geometry=Point(0, 0, 0))

    # ==========================================================================
    # serialize the model_node
    # =========================================================================
    json_dump(group_node, "data/model_how_to_use_it_model_node.json", pretty=True)

    # ==========================================================================
    # deserialize the model_node
    # ==========================================================================
    model_node_deserialized = json_load("data/model_how_to_use_it_model_node.json")

    # ==========================================================================
    # print the contents of the deserialized model_node
    # ==========================================================================
    print("model_node:              ", group_node)
    print("model_node_deserialized: ", model_node_deserialized)

    # ==========================================================================
    # create elements and a Node
    # ==========================================================================
    element_node = ElementNode(name="spoke1", element=Element.from_frame(1, 10, 1))  # type: ignore

    # ==========================================================================
    # serialize the model_node
    # =========================================================================
    json_dump(element_node, "data/model_how_to_use_it_model_node.json", pretty=True)

    # ==========================================================================
    # deserialize the model_node
    # ==========================================================================
    element_node_deserialized = json_load("data/model_how_to_use_it_model_node.json")

    # ==========================================================================
    # print the contents of the deserialized model_node
    # ==========================================================================
    print("element_node:              ", element_node, element_node.element.geometry)
    print(
        "element_node_deserialized: ",
        element_node_deserialized,
        element_node_deserialized.element.geometry,
    )


def serialize_model_tree():

    # ==========================================================================
    # create model
    # ==========================================================================
    model = create_model()

    # ==========================================================================
    # serialize the model_tree
    # ==========================================================================
    json_dump(model.hierarchy, "data/model_how_to_use_it_model_tree.json", pretty=True)

    # ==========================================================================
    # deserialize the model_tree
    # ==========================================================================
    model_tree_deserialized = json_load("data/model_how_to_use_it_model_tree.json")

    # ==========================================================================
    # print the contents of the deserialized model_tree
    # ==========================================================================
    # model.hierarchy.print()
    model_tree_deserialized.print()  # type: ignore


def serialize_model():
    # ==========================================================================
    # create model
    # ==========================================================================
    model = create_model_with_interactions()

    # ==========================================================================
    # serialize the model_tree
    # ==========================================================================
    # print(model)
    json_dump(model, "data/model_how_to_use_it_model.json", pretty=True)

    # ==========================================================================
    # deserialize the model_tree
    # ==========================================================================
    model_deserialized = json_load("data/model_how_to_use_it_model.json")

    # ==========================================================================
    # print the contents of the deserialized model_tree
    # ==========================================================================
    model.print()
    model_deserialized.print()


if __name__ == "__main__":
    model = create_model().print()
    # model = create_model_with_interactions()
    # model = create_model_without_hierarchy()

    # copy_model()

    # serialize_element()
    # serialize_model_node()
    # serialize_model_tree()
    # serialize_model()
