from compas.geometry import Point
from compas_model.elements import Element
from compas_model.model import ElementNode
from compas_model.model import GroupNode
from compas_model.model import Model
from compas.data import json_dump, json_load
from compas.datastructures import Mesh


def create_model():
    """Create a model with a hierarchy of groups and elements."""

    # --------------------------------------------------------------------------
    # create model
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # add group nodes - a typical tree node with a name and geometry
    # --------------------------------------------------------------------------
    car = model.add_group(name="car", geometry=None)
    wheel = car.add_group(name="wheel", geometry=Point(0, 0, 0))

    # --------------------------------------------------------------------------
    # add element nodes - a "special" tree node with a name and element
    # --------------------------------------------------------------------------
    wheel.add_element(name="spoke1", element=Element.from_frame(1, 10, 1))
    wheel.add_element(name="spoke2", element=Element.from_frame(5, 10, 1))
    wheel.add_element(name="spoke3", element=Element.from_frame(10, 10, 1))

    # --------------------------------------------------------------------------
    # print the model to preview the tree structure
    # --------------------------------------------------------------------------
    model.print()

    return model


def create_model_with_interactions():
    """Create a model with a hierarchy of groups and elements and interactions."""

    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = Model()

    # --------------------------------------------------------------------------
    # Add group nodes - a typical tree node with a name and geometry.
    # --------------------------------------------------------------------------
    car = model.add_group(name="car", geometry=None)  # type: ignore
    wheel = car.add_group(name="wheel", geometry=Point(0, 0, 0))  # type: ignore

    # --------------------------------------------------------------------------
    # Add element nodes - a "special" tree node with a name and element.
    # --------------------------------------------------------------------------
    spoke1 = wheel.add_element(name="spoke1", element=Element.from_box_dimensions(1, 10, 1))  # type: ignore
    spoke2 = wheel.add_element(name="spoke2", element=Element.from_box_dimensions(5, 10, 1))  # type: ignore
    spoke3 = wheel.add_element(name="spoke3", element=Element.from_box_dimensions(10, 10, 1))  # type: ignore

    # --------------------------------------------------------------------------
    # Add interactions.
    # --------------------------------------------------------------------------
    model.add_interaction(spoke1, spoke2)
    model.add_interaction(spoke1, spoke3)
    model.add_interaction(spoke2, spoke3)

    # --------------------------------------------------------------------------
    # Print the model to preview the tree structure.
    # --------------------------------------------------------------------------
    model.print()

    # --------------------------------------------------------------------------
    # Output.
    # --------------------------------------------------------------------------
    return model


def copy_model():
    """Copy a model and all its attributes."""
    # --------------------------------------------------------------------------
    # Create elements and a Node and a ElementTree and a Model.
    # --------------------------------------------------------------------------
    e0 = Element(
        name="beam",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e1 = Element(
        name="beam",
        geometry_simplified=Point(0, 5, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e2 = Element(
        name="block",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    e3 = Element(
        name="block",
        geometry_simplified=Point(0, 5, 0),
        geometry=Mesh.from_polyhedron(6),
    )

    model = (
        Model()
    )  # the root of hierarchy automatically initializes the root node as <my_model>
    truss1 = model.add_group("truss1")
    truss2 = model.add_group("truss2")
    truss1.add_element(e0.name, e0)
    truss1.add_element(e1.name, e1)
    truss2.add_element(e2.name, e2)
    truss2.add_element(e3.name, e3)

    model.add_interaction(e0, e1)

    print("BEFORE COPY")
    model.print()
    model.print_interactions()
    # --------------------------------------------------------------------------
    # Copy the model.
    # --------------------------------------------------------------------------
    print("AFTER COPY")
    model_copy = model.copy()
    model_copy.print()
    model_copy.print_interactions()


def serialize_element():
    """Serialize an element to a JSON file."""
    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    e = Element(
        name="beam",
        geometry_simplified=Point(0, 0, 0),
        geometry=Mesh.from_polyhedron(6),
    )
    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # =========================================================================
    print(e)
    json_dump(e, "data/model_how_to_use_it_element.json", pretty=True)
    json_load("data/model_how_to_use_it_element.json")
    print(e)


def serialize_model_node():
    """Serialize a model_node and the elements inside."""
    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    group_node = GroupNode(name="timber1", geometry=Point(0, 0, 0))

    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # =========================================================================
    json_dump(group_node, "data/model_how_to_use_it_model_node.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_node.
    # --------------------------------------------------------------------------
    model_node_deserialized = json_load("data/model_how_to_use_it_model_node.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_node.
    # --------------------------------------------------------------------------
    print("model_node:              ", group_node)
    print("model_node_deserialized: ", model_node_deserialized)

    # --------------------------------------------------------------------------
    # Create elements and a Node.
    # --------------------------------------------------------------------------
    element_node = ElementNode(name="spoke1", element=Element.from_box_dimensions(1, 10, 1))  # type: ignore

    # --------------------------------------------------------------------------
    # Serialize the model_node.
    # =========================================================================
    json_dump(element_node, "data/model_how_to_use_it_model_node.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_node.
    # --------------------------------------------------------------------------
    element_node_deserialized = json_load("data/model_how_to_use_it_model_node.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_node.
    # --------------------------------------------------------------------------
    print("element_node:              ", element_node, element_node.element.geometry)
    print(
        "element_node_deserialized: ",
        element_node_deserialized,
        element_node_deserialized.element.geometry,
    )


def serialize_model_tree():
    """Serialize a model_tree and nodes and the elements inside."""
    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = create_model()

    # --------------------------------------------------------------------------
    # Serialize the model_tree.
    # --------------------------------------------------------------------------
    json_dump(model.hierarchy, "data/model_how_to_use_it_model_tree.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_tree.
    # --------------------------------------------------------------------------
    model_tree_deserialized = json_load("data/model_how_to_use_it_model_tree.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_tree.
    # --------------------------------------------------------------------------
    model.hierarchy.print()

    print()
    model_tree_deserialized.print()  # type: ignore


def serialize_model():
    """Serialize a model and its graph and a model_tree and nodes and the elements inside."""
    # --------------------------------------------------------------------------
    # Create model.
    # --------------------------------------------------------------------------
    model = create_model_with_interactions()

    # --------------------------------------------------------------------------
    # Serialize the model_tree.
    # --------------------------------------------------------------------------
    # print(model)
    json_dump(model, "data/model_how_to_use_it_model.json", pretty=True)

    # --------------------------------------------------------------------------
    # Deserialize the model_tree.
    # --------------------------------------------------------------------------
    model_deserialized = json_load("data/model_how_to_use_it_model.json")

    # --------------------------------------------------------------------------
    # Print the contents of the deserialized model_tree.
    # --------------------------------------------------------------------------
    model.print()
    model_deserialized.print()


if __name__ == "__main__":
    model = create_model()
    # model = create_model_with_interactions()

    # copy_model()

    # serialize_element()
    # serialize_model_node()
    # serialize_model_tree()
    # serialize_model()
