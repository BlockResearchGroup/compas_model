# import random
import pytest
from compas.geometry import Box
from compas.tolerance import TOL
from compas_model.algorithms import brep_brep_contacts
from compas_model.algorithms import mesh_mesh_contacts


@pytest.mark.parametrize(
    ["vector", "size"],
    [
        ([1, 0, 0], 1),
        ([0, 1, 0], 1),
        ([0, 0, 1], 1),
        ([1, 0.5, 0], 0.5),
        ([1, 0, 0.5], 0.5),
        ([1, 0.5, 0.5], 0.25),
        ([0.5, 1, 0], 0.5),
        ([0, 1, 0.5], 0.5),
        ([0.5, 1, 0.5], 0.25),
        ([0.5, 0, 1], 0.5),
        ([0, 0.5, 1], 0.5),
        ([0.5, 0.5, 1], 0.25),
    ],
)
def test_brep_brep_contacts(vector, size):
    # Create two cubes
    box1 = Box(1, 1, 1)
    box2 = Box(1, 1, 1)

    # Move box2 to overlap with box1
    box2.translate(vector)

    # Convert boxes to BReps
    box1_brep = box1.to_brep()
    box2_brep = box2.to_brep()

    # Find contacts between the two BReps
    contacts = brep_brep_contacts(box1_brep, box2_brep)

    # Check that contacts were found
    assert len(contacts) > 0
    assert len(contacts) == 1

    # Check that the contacts are indeed overlapping
    for contact in contacts:
        assert contact.size > 0
        assert TOL.is_close(contact.size, size)


@pytest.mark.parametrize(
    ["vector", "size"],
    [
        ([1, 0, 0], 1),
        ([0, 1, 0], 1),
        ([0, 0, 1], 1),
        ([1, 0.5, 0], 0.5),
        ([1, 0, 0.5], 0.5),
        ([1, 0.5, 0.5], 0.25),
        ([0.5, 1, 0], 0.5),
        ([0, 1, 0.5], 0.5),
        ([0.5, 1, 0.5], 0.25),
        ([0.5, 0, 1], 0.5),
        ([0, 0.5, 1], 0.5),
        ([0.5, 0.5, 1], 0.25),
    ],
)
def test_mesh_mesh_contacts(vector, size):
    # Create two cubes
    box1 = Box(1, 1, 1)
    box2 = Box(1, 1, 1)

    # Move box2 to overlap with box1
    box2.translate(vector)

    # Convert boxes to BReps
    box1_mesh = box1.to_mesh()
    box2_mesh = box2.to_mesh()

    # Find contacts between the two BReps
    contacts = mesh_mesh_contacts(box1_mesh, box2_mesh)

    # Check that contacts were found
    assert len(contacts) > 0
    assert len(contacts) == 1

    # Check that the contacts are indeed overlapping
    for contact in contacts:
        assert contact.size > 0
        assert TOL.is_close(contact.size, size)
